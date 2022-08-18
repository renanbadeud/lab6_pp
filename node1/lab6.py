from base64 import encode
from cmath import e
from ctypes import sizeof
from email.base64mime import body_decode
from gc import callbacks
from inspect import Signature, signature
from itertools import count
from ssl import CHANNEL_BINDING_TYPES
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
import pika, sys, os
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
import json
import pandas as pd
import pika, sys, os
import threading
import random
import string
from hashlib import sha1
import uuid
from seed_utils import Seed

global arquivo 
arquivo = 'banco-de-dados.csv'

def getTransactionID():
    try:
        df = pd.read_csv(arquivo)
    except:
        df = None
    transactionID = 0
    
    if(df is None):
        lista = {"TransactionID":[0], "Challenge":[random.randint(1,20)], "Seed":[" "], "Winner": [-1]}
        df = pd.DataFrame(lista)
    else:
        tam = len(df.iloc[:, 0])
        if(df.iloc[tam-1, 3] == -1):
            return int(df.iloc[tam-1, 0])
        else:
            transactionID = int(df.iloc[(tam-1), 0])+1
            lista = {"TransactionID":transactionID, "Challenge":[random.randint(1,20)], "Seed":[" "], "Winner": [-1]}
            transaction = pd.DataFrame(lista)

            df = pd.concat([df,transaction], ignore_index = True)
    
    df.to_csv(arquivo, index=False)
    
    return int(transactionID)

def getChallenge():
    try:
        df = pd.read_csv(arquivo)
    except:
        return -1
    challenge = df.iloc[-1, 1]
    return challenge

def random_id():
    id=(uuid.uuid4().int)
    mask = (1 << 32) -1
    return id&mask

def save_pubkey(id, pubkey):
    filename = id + ".txt"
    content = pubkey
    lines = ['-----BEGIN PUBLIC KEY-----',content,'-----END PUBLIC KEY-----']
    with open(filename, 'w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')
    f.close()

def verify_message(msg, signature):
    message = msg

    digest = SHA256.new()
    digest.update(message.encode('utf-8'))
    message = json.loads(msg)
    sig = signature
    sig = bytes.fromhex(sig)  # convert string to bytes object

    # Load public key (not private key) and verify signature
    public_key = RSA.importKey(open(str(message.get('NodeId'))+".txt").read())    ## FAZER COM Q O ARQUIVO SEJA CORRESPONDENTE AO REMETENTE ##
    verifier = PKCS1_v1_5.new(public_key)
    verified = verifier.verify(digest, sig)

    if verified:
        return True
    else:
        return False

def share_pubkey():
    #Load public key previouly generated
    data = open("public_key.txt",'r').read() 
    msg = data.split("\n")
    msg = msg[1:-1]
    pubkey =''.join(msg)
    return str(pubkey)

def sign_message(msg):
    message = json.dumps(msg)
    digest = SHA256.new()
    digest.update(message.encode('utf-8'))

    #Load private key previouly generated
    with open("private_key.pem", "r") as myfile:
        private_key = RSA.importKey(myfile.read())
    myfile.close()

    # Sign the message
    signer = PKCS1_v1_5.new(private_key)
    sig = signer.sign(digest)
    msgsinged = str(sig.hex())
    
    return msgsinged

def verificaSEED(hash, challenger):
    for i in range(0,40):
        ini_string = hash[i]
        scale = 16
        res = bin(int(ini_string, scale)).zfill(4)
        res = str(res)
        for k in range(len(res)):
            if(res[k] == "b"):
                res = "0"*(4-len(res[k+1:]))+res[k+1:]
                break

        for j in range (0, 4):
            if(challenger == 0):
                if(res[j] != "0"):
                    return 1
                else:
                    return -1
            if(res[j] == "0"):
                challenger = challenger - 1
            else:
                return -1
    return -1

def main():
    users = []
    users_pubkey = []
    election = []
    votes = []
    qtd_usuarios = int(input("Quantidade de usuarios do sistema: "))

    NodeId =	{
        "NodeId": ' '
    }  
    NodeId['NodeId'] = random_id()
    NodeId = json.dumps(NodeId)
    numero = '1' 

    #ESPERA 'n' PARTICIPANTES ENVIAREM O NodeId
    def init(ch, method, properties, body): 
        user = json.loads(body.decode())
        if(len(users) == 0):
            users.append(user)
            channel.basic_publish(exchange = 'ppd/init', routing_key = '', body = NodeId)
        elif(len(users) <= qtd_usuarios):
            for x in users:
                if(x != user):
                    channel.basic_publish(exchange = 'ppd/init', routing_key = '', body = NodeId)
                    users.append(user)
                if(len(users) == qtd_usuarios):
                    dic = json.loads(NodeId)
                    pubkey = share_pubkey()
                    msg = { "NodeId": dic.get("NodeId"), "PubKey" :pubkey}
                    msg = json.dumps(msg)
                    channel.basic_publish(exchange = 'ppd/pubkey', routing_key = '', body = msg)
        else:
            print("Sala cheia!!")

    #TROCA DE CHAVE PUBLICA ENTRE PARTICIPANTES
    def troca_chaves(ch, method, properties, body): 
        message_json = json.loads(body.decode())
        for x in users:
            if(message_json.get('NodeId') == x.get('NodeId')):
                if(len(users_pubkey) == 0):
                    users_pubkey.append(message_json)
                    id = str(message_json.get("NodeId"))
                    pubkey = message_json.get("PubKey")
                    save_pubkey(id, pubkey)
                    break
                for y in users_pubkey:
                    if(message_json != y):
                        users_pubkey.append(message_json)
                        id = str(message_json.get("NodeId"))
                        pubkey = message_json.get("PubKey")
                        save_pubkey(id, pubkey)
                        break
        if(len(users_pubkey) == qtd_usuarios):
            dic = json.loads(NodeId)
            number = random_id()
            vote = { "NodeId": dic.get("NodeId"), "ElectionNumber" : number}
            sig = sign_message(vote)
            message_vote = { "NodeId": dic.get("NodeId"), "ElectionNumber" : number, "Sign": sig}
            message_vote = json.dumps(message_vote)
            channel.basic_publish(exchange = 'ppd/election', routing_key = '', body = message_vote)
                
    #ELEICAO
    def eleicao(ch, method, properties, body):
        message = body.decode()
        message = json.loads(message)
        for x in users:
            if(message.get('NodeId') == x.get('NodeId')):
                if(len(election) == 0):
                    election.append(message)
                    break
                for y in election:
                    if(message != y):
                        election.append(message)

        if(len(election) == qtd_usuarios):
            elec_number = -1
            
            for temp in election: # ------------------------------------------------------------------- #
                signature = temp.get('Sign')
                del temp["Sign"]

                msg = json.dumps(temp)
                if(verify_message(msg, signature)):
                    if(temp.get('ElectionNumber') > elec_number):
                        leader = temp
                        elec_number = leader.get('ElectionNumber')
                    elif(temp.get('ElectionNumber') == elec_number):
                        if(temp.get('NodeId') > leader.get('NodeId')):
                            leader = temp
                else:
                    print("Messagem fraudada: " + json.dumps(temp))
            
            print("Resultado da Eleicao: " + json.dumps(leader))

            pad = json.loads(NodeId) 

            if(pad.get("NodeId") == leader.get("NodeId")):
                transactionID = getTransactionID()  
                challenger = getChallenge()
                
                challenge = {"NodeId": leader.get("NodeId"), "TransactionNumber": transactionID,"Challenge": int(challenger)}
                sig = sign_message(challenge)
                challenge_msg = {"NodeId": leader.get("NodeId"), "TransactionNumber": transactionID, "Challenge": int(challenger), "Sign": sig}
                challenge_msg = json.dumps(challenge_msg)
                channel.basic_publish(exchange = 'ppd/challenge', routing_key = '', body = challenge_msg)

            election.clear()

    #PROCURA SLÇ P/ CHALLENGE
    def procura_seed(ch, method, properties, body):
        #CRIAR TABELA AQUI!!!!!
        message = json.loads(body.decode())
        
        try:
            df = pd.read_csv(arquivo)
        except:
            df = None
        if(df is None):
            lista = {"TransactionID":message.get("TransactionNumber"), "Challenge":message.get("Challenge"), "Seed":[" "], "Winner": [-1]}
            df = pd.DataFrame(lista)
        else:
            tam = len(df.iloc[:, 0])
            if(df.iloc[tam-1, 3] == -1):
                pass
            else:
                transactionID = int(df.iloc[(tam-1), 0])+1
                lista = {"TransactionID":message.get("TransactionNumber"), "Challenge":message.get("Challenge"), "Seed":[" "], "Winner": [-1]}
                transaction = pd.DataFrame(lista)

                df = pd.concat([df,transaction], ignore_index = True)

        df.to_csv(arquivo, index=False)
        
        # *¨¨¨¨¨* GRAVAR ID DO LIDER *¨¨¨¨¨* #
        
        signature = message.get('Sign')
        del message["Sign"]
        msg = json.dumps(message)

        if(verify_message(msg, signature)):
            seed = []
            msg = json.loads(msg)
            challenger = msg.get('Challenge')

            # Buscar, localmente, uma seed (semente) que solucione o desafio proposto
            flag = True

            def getSeed2(challenger, seed, size):
                while(flag):
                    seedTemp = Seed.generate_random()
                    if (Seed.check_seed(Seed(), challenger, seedTemp)):
                        seed.append(seedTemp)
                        break

            multThread = []

            for i in range(1,challenger*2+1):
                thread = threading.Thread(target=getSeed2, args=(challenger, seed, i, ))
                multThread.append(thread)
                thread.start()
                
                if(len(seed) > 0):
                    flag = False
                    break   

            while(True):
                if(len(seed) != 0):
                    break

            flag = False

            # Verifica se todas as threads acabaram 
            for thread in multThread:
                thread.join()

        id = json.loads(NodeId)
        transactionID = msg.get("TransactionNumber") #getTransactionID()

        seed_msg = {'NodeId': id.get('NodeId'), 'TransactionNumber': transactionID, 'Seed': seed[0]}
        sig = sign_message(seed_msg)
        seed_msg = {'NodeId': id.get('NodeId'), 'TransactionNumber': transactionID, 'Seed': seed[0], 'Sign': sig}
        seed_msg = json.dumps(seed_msg)
        channel.basic_publish(exchange = 'ppd/solution', routing_key = '', body = seed_msg)

        ##VERIFICAR SE PODE FAZER ISSO##
        voting = {'NodeId': id.get('NodeId'), "TransactionNumber": transactionID, "Seed": seed[0],'Vote': 1, 'SolutionID': id.get('NodeId')}
        sig = sign_message(voting)
        voting_msg = {'NodeId': id.get('NodeId'), "TransactionNumber": transactionID, "Seed": seed[0], 'Vote': 1, 'SolutionID': id.get('NodeId'),'Sign': sig}
        voting_msg = json.dumps(voting_msg)
        channel.basic_publish(exchange = 'ppd/voting', routing_key = '', body = voting_msg)

    #CONFERE SLÇ E VOTA
    def votacao(ch, method, properties, body):
        message = body.decode()
        message = json.loads(message)        
        signature = message.get('Sign')
        del message["Sign"]
        msg = json.dumps(message)
        if(verify_message(msg, signature)):
            msg = json.loads(msg)
            challenger = getChallenge()
            transactionID = msg.get('TransactionNumber')
            seed = msg.get('Seed')

            if(Seed.check_seed(Seed(), challenger, seed) == True):
                id = json.loads(NodeId)
                voting = {'NodeId': id.get('NodeId'), "TransactionNumber": transactionID, "Seed": seed,'Vote': 1, 'SolutionID': msg.get('NodeId')}
                sig = sign_message(voting)
                voting_msg = {'NodeId': id.get('NodeId'), "TransactionNumber": transactionID, "Seed": seed, 'Vote': 1, 'SolutionID': msg.get('NodeId'),'Sign': sig}
                voting_msg = json.dumps(voting_msg)
                channel.basic_publish(exchange = 'ppd/voting', routing_key = '', body = voting_msg)
            else:
                id = json.loads(NodeId)
                voting = {'NodeId': id.get('NodeId'), "TransactionNumber": transactionID, "Seed": seed, 'Vote': 0, 'SolutionID': msg.get('NodeId')}
                sig = sign_message(voting)
                voting_msg = {'NodeId': id.get('NodeId'), "TransactionNumber": transactionID, "Seed": seed, 'Vote': 0, 'SolutionID': msg.get('NodeId'),'Sign': sig}
                voting_msg = json.dumps(voting_msg)
                channel.basic_publish(exchange = 'ppd/voting', routing_key = '', body = voting_msg)
        else: 
            print('Menssagem Fraudada!!')

    #CONTABILIZA VOTOS
    def checa_votos(ch, method, properties, body):
        count = 0
        message = body.decode()
        message = json.loads(message)

        #ADICIONA O VOTO NA LISTA DE VOTOS SE A MENSAGEM ENVIADA FOR DIFERENTE
        for x in users:
            if(message.get('NodeId') == x.get('NodeId')):
                if(len(votes) == 0):
                    votes.append(message)
                    break
                for y in votes:
                    if(message != y):
                        votes.append(message)    
        
        #CONTABILIZA VOTOS
        if(len(votes) == qtd_usuarios):
            for x in votes:
                signature = x.get('Sign')
                del x["Sign"]
                msg = json.dumps(x)
                if(verify_message(msg, signature)):   
                    msg = json.loads(msg)
                    if(msg.get('Vote') == 1):
                        count += 1
                    if(count >= (int)(qtd_usuarios/2+1)):
                        try:
                            df = pd.read_csv(arquivo)
                        except:
                            return -1 
                        if(df.iloc[-1]['Winner'] == -1):
                            transactionID = getTransactionID()
                            trasition = df.query("TransactionID == "+str(transactionID))  
                    
                            trasition.loc[transactionID,"Seed"]   = msg.get('Seed')
                            trasition.loc[transactionID,"Winner"] = msg.get('SolutionID')
                    
                            df.iloc[transactionID,:] = trasition.iloc[0,:]
                    
                            df.to_csv(arquivo, index=False)
                            tabela = pd.read_csv(arquivo)
                            print(tabela)
                            # enviar uma mensagem para eleger uma novo lider
                            id = json.loads(NodeId)
                            number = random_id()
                            elec = { "NodeId": id.get("NodeId"), "ElectionNumber" : number}
                            sig = sign_message(elec)
                            elec_msg = { "NodeId": id.get("NodeId"), "ElectionNumber" : number, 'Sign': sig}
                            elec_msg = json.dumps(elec_msg)
                            channel.basic_publish(exchange = 'ppd/election', routing_key = '', body = elec_msg)
                else:
                    print("Mensagem Fraudada!!")
            votes.clear()
    
    credentials = pika.credentials.PlainCredentials("admin", "admin")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='10.9.13.101', credentials=credentials))

    channel = connection.channel()

    channel.exchange_declare(exchange ='ppd/init', exchange_type ='fanout')
    room = channel.queue_declare(queue = 'ppd/init/'+numero)      # assina/publica - Sala de Espera
    channel.queue_bind(exchange = 'ppd/init', queue = room.method.queue)

    channel.exchange_declare(exchange = 'ppd/pubkey', exchange_type ='fanout')
    room = channel.queue_declare(queue = 'ppd/pubkey/'+numero)      # assina/publica - Fila de Chaves Publicas
    channel.queue_bind(exchange = 'ppd/pubkey', queue = room.method.queue)
    
    channel.exchange_declare(exchange = 'ppd/election', exchange_type ='fanout')
    room = channel.queue_declare(queue = 'ppd/election/'+numero)      # assina/publica - Fila de Eleicao
    channel.queue_bind(exchange = 'ppd/election', queue = room.method.queue)

    channel.exchange_declare(exchange = 'ppd/challenge', exchange_type ='fanout')
    room = channel.queue_declare(queue = 'ppd/challenge/'+numero)      # assina/publica - Fila de Desafios
    channel.queue_bind(exchange = 'ppd/challenge', queue = room.method.queue)

    channel.exchange_declare(exchange = 'ppd/solution', exchange_type ='fanout')
    room = channel.queue_declare(queue = 'ppd/solution/'+numero)      # assina/publica - Fila de Solucoes
    channel.queue_bind(exchange = 'ppd/solution', queue = room.method.queue)

    channel.exchange_declare(exchange = 'ppd/voting', exchange_type ='fanout')
    room = channel.queue_declare(queue = 'ppd/voting/'+numero)      # assina/publica - Fila de Votacao
    channel.queue_bind(exchange = 'ppd/voting', queue = room.method.queue)

    channel.basic_publish(exchange = 'ppd/init', routing_key = '', body = NodeId)

    channel.basic_consume(queue = 'ppd/init/'+numero , on_message_callback = init, auto_ack = True)
    channel.basic_consume(queue = 'ppd/pubkey/'+numero , on_message_callback = troca_chaves, auto_ack = True)
    channel.basic_consume(queue = 'ppd/election/'+numero , on_message_callback = eleicao, auto_ack = True)
    channel.basic_consume(queue = 'ppd/challenge/'+numero , on_message_callback = procura_seed, auto_ack = True)
    channel.basic_consume(queue = 'ppd/solution/'+numero , on_message_callback = votacao, auto_ack = True)
    channel.basic_consume(queue = 'ppd/voting/'+numero , on_message_callback = checa_votos, auto_ack = True)
    
    channel.start_consuming()


if __name__ == '__main__':
    try:
        file = 'banco-de-dados.csv'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)   
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
