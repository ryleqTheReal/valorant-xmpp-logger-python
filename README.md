# Riot Client - Server Middleman

This is a communication logger for the requests between riot client and riot server. Currently this is the only approach to see party ID's and therefore tell who is queued up with who and see chat messages in **VALORANT**.

This project just rewrites the already existing [Valorant XMPP Logger by techchrism](https://github.com/techchrism/valorant-xmpp-logger/tree/trunk), which is in typescript, into the more comprehensible python.

# Usage

NOTE: *I have never used git*

  - Download the folder
  - Open the console
  - Change the directory to the project in cmd: `cd "<path to project folder>"`
  - Run `pip install -r requirements.txt` in your console
  - Run `python "<path to project folder>"`

# Log Format

NOTE: *I am just going to rewrite [@Techchrisms](https://github.com/techchrism) description for this*

- type:
  - `incoming`: messages incoming from the chat server to the riot client
    - `time`: the timestamp of when the message was received
    - `data`: the transmitted data (often in unfinished chunks)
      
  - `outgoing`: messages going out from the riot client to the riot server (mostly XML for authentication)
    - `time`: the timestamp of when the message was received
    - `data`: the transmitted data (often in unfinished chunks)
      
  - `open-valorant`: logs when the program connects to a chat-server:
    - `time`: the timestamp of when the message was received
    - `host`: the hostname of the Riot XMPP server that the connection is intended for
    - `port`:  the port of the Riot XMPP server that the connection is intended for
    - `socketID`: the ID of which socket of the program the message comes from (in case the program opens multiple communication sockets to differenciate them)

Most of the communication happens in `XML` which is oftentimes sent in chunks, if you happen to implement a logic for handling those chunks, you're welcome to add it to the code!

# Motivation

After the party endpoints got changed to only be used on oneself, the lack of possibility to see parties and chatmessages motivated me to try and implement it myself. However because I am not used to typescript I rewrote it into python.
This also facilitates it for other developers to comprehend the code and maybe implement it into great projects like [the Valorant Rank Yoinker by Zay](https://github.com/zayKenyon/VALORANT-rank-yoinker). 



