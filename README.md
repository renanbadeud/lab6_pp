# lab6_pp
Grupo: Milena, Lorenzo, Renan

## Funcionamento:

Para entrar na rede cada nó envia seu NodeId (utilizado UUID convertido para inteiro de 32 bits) para 
os demais a fim de ser identificado. Em seguida é realizada a troca de chaves públicas(salvas em arquivos de nome NodeId + ".txt"). Posteriormente,
é feita a eleição do líder,o dono do maior NodeId é o líder. O líder envia o challenge para todos os nós, cada nó busca busca a seed que soluciona o desafio, e assim que a encontra, submete aos demais nós que verificam se ela é válida,se a maioria dos nós validarem a seed, o nó que a submeteu vence.
O processo se repete, o challenge muda a cada iteração e o líder também.

Utilizada exchange do tipo fanout, que copia e roteia as mensagems recebidas para todas as filas que estão vinculadas a ela.

Exceto as exchanges 'ppd/init' e 'ppd/pubkey', as demais exchanges tem as mensagens assinadas pelo autor (NodeId) e sempre é checada a veracidade da 
informação, conforme especificação.

Cada fila tem uma função de callback diferente, que será acionada quando as mensagens forem recebidas.

## Validação da seed e estratégia de brute force: 
Foi criada a função check_seed para validar seeds garantindo que estejam em conformidade com o alfabeto 
descrito e que seja uma seed que resolva o desafio. Depois de checar se a seed possui somente caracteres
permitidos, a função aplica o algoritmo SHA-1 na seed e checa se o tamanho prefixo de bits 0 na hash tem 
tamanho maior ou igual ao número do desafio.
A estratégia para brute force foi fazer uso de threads que geram strings aleatórias de tamanho aleatório entre 
10 e 100, assim a probabilidade de testar strings duplicadas é aproximadamente 0.

## Exchanges utilizadas:

- 'ppd/init': entrada dos nós na rede.
- 'ppd/pubkey': troca das chaves públicas entre os participantes do sistema. 
- 'ppd/election': eleição do líder.
- 'ppd/challenge': nós recebem os desafios.
- 'ppd/solution': onde é recebido a solução do desafio.
- 'ppd/voting': votação para a validação do desafio.

## Requerimentos:
- python3 -m pip install --upgrade pika
- pip3 install -U PyCryptodome
- sudo apt install python3-pandas
- pip3 install threading
- pip install python-time

## Executando o código:
Entre na pasta node1 , abra o terminal e rode python3 lab6.py
