# lab6_pp

## Funcionamento:

Para entrar na rede cada nó envia seu NodeId (utilizado UUID convertido para inteiro de 32 bits) para 
os demais a fim de ser identificado. Em seguida é realizada a troca de chaves públicas(salvas em arquivos de nome NodeId + ".txt"). Posteriormente,
é feita a eleição do líder,o dono do maior NodeId é o líder. O líder envia o challenge para todos os nós, cada nó busca busca a seed que soluciona o desafio, e assim que a encontra, submete aos demais nós que verificam se ela é válida,se a maioria dos nós validarem a seed, o nó que a submeteu vence.
O processo se repete, o challenge muda a cada iteração e o líder também.

Utilizada exchange do tipo fanout, que copia e roteia as mensagems recebidas para todas as filas que estão vinculadas a ela.
Um mesmo callback para o recebimento de todas as exchanges é utilizado, sendo encaminhado para os devidos fins de acordo com os itens presentes na mensagem.
Exceto as exchanges 'ppd/init' e 'ppd/pubkey', as demais exchanges tem as mensagens assinadas pelo autor (`NodeId`) e sempre é checada a veracidade da 
informação, conforme especificação.
Cada fila tem uma função de callback diferente, que será acionada quando as mensagens forem recebidas.




## Exchanges utilizadas:

- 'ppd/init': entrada dos nós na rede.
- 'ppd/pubkey': troca das chaves públicas entre os participantes do sistema. 
- 'ppd/election': eleição do líder.
- 'ppd/challenge': nós recebem os desafios.
- 'ppd/solution': onde é recebido a solução do desafio.
- 'ppd/voting': votação para a validação do desafio.

