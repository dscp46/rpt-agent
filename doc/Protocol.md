# Repeater Remote Control Protocol (RRCP)

## Status of this document

This memo is currently a DRAFT. Its content SHALL NOT be interpreted as informatory for the moment.

<!-- This memo provides information for the Internet community. It does not specify an Internet standard of any kind. Distribution of this memo is unlimited. -->

## Abstract

This document describes RRCP, a protocol designed to control, monitor, and to trigger provisioning of amateur radio repeaters.

## Rationale

With the growing size of our regional repeater network, the ability to perform basic maintenance (connecting to, or disconnecting from, a module, enabling, disabling or rebooting the system) has become challenging due to the number of involved parties, their varying proficiency with CLI, their respective availability, and some of our repeaters are not easily reachable, from a network perspective.

Due to the way our repeaters system images are built and to the administrative topology of our network, doing proper and reliable privilege isolation and rights management can prove difficult. 

In the future, we're planning to add the ability to remotely trigger the remote control agent's update, automatic and easy conference provisionning, including from a fresh install (flash the system image on your repeater logic, let it announce itself, then set it up remotely).

## Preliminary Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

In the following parts of this document:
  - The hardware device that needs to me remotely operated will be referred as a **controlled device**.
  - The resident software process that runs on a repeater and listens for commands, to remotely control it, will be defined as an **agent**.
  - The software that is used to send commands to control a repeater will be called a **control client**.
  - The software, to which a control client will connect to, is designated as a **message broker**.
  - A group on which multiple controlled devices connect to, with the purpose of collectively exchanging voice or data signals (A.K.A a *conference*, a *reflector*, a *room*, or a *talk group*) will be called a **module**.
  - A **message** is a RRCP datagram exchanged by two of the following: control client, controlled device, message broker.

### Cryptographic material definition
  - The **session key**, noted **Ks**, known to both by the message broker and the agent, is used to generate the Message Integrity Tag, if applicable. Details on how this message is generated will be described later in this document.
  - The **association key**, noted **Ka**, known to both by the message broker and the agent, is used to negociate a new session key during the Join procedure.

## Protocol definition
The Repeater Remote Control Protocol (RRCP) is built on top either of the following:
  - MQTT (ISO/IEC 20922:2016)
  - LoRaWAN
  - AX.25 UI Frames following the APRS standard

### RRCP over MQTT
This variant of RRCP enables the remote control of a repeater over an IP network (either over Hamnet or over the Internet).

The MQTT protocol version used by an agent or a control client is not specified, and left at the discretion of the message broker's administrator.
  
The MQTT username, noted `<callsign>` in this document, SHOULD be the lowercase alphanumerical form, plus dash and underscore of the repeater callsign. The underscore is used to replace the slash character in a callsign. As an example, `F8KLY/P-S` used for a portable simplex hotspot by F8KLY, will be encoded as `f8kly_p-s`.

When an agent connects to the message broker, it subscribes to the topic `repeaters/<callsign>/v1` for QoS level 0 and 2, then listens for incoming messages.

When an agent receives a valid message with QoS level 2 it MUST send back an acknowledgement with QoS level 2. Acknowledgements MUST be sent to the topic `repeaters/<callsign>/v1/response`.

Replies to valid, supported messages sent with QoS level 0 is OPTIONAL. The control client SHALL send a message with QoS level 2 if it expects a reply.

An agent SHALL NOT reply to invalid messages, or to valid messages that refer to an unimplemented feature.

This acknowledgement SHOULD be sent after the command has been successfully executed. In specific cases, such as a system reboot, the response MAY be sent prior to executing the action.

If the agent is able to send advertisements, it MUST send them to the topic `repeaters/<callsign>/v1/advertise`. A control client SHOULD subscribe to `repeaters/+/v1/advertise` to get a realtime overview of the repeaters he's got in sight.

#### Command Message format
There are 3 fields in a command message (the last one is optional), separated by the space character:
  - The message Sequence number (SEQ): an unsigned integer represented in its decimal form. Valid values include any integer from 1 to 19 digits.
  - The command (CMD)
  - The Arguement (ARG) 
  
```ABNF
DIGIT            =  %x30-39
SP               =  %x20
VCHAR            =  %x21-7E                  ; Printable characters
cmd              =  1*VCHAR                  ; Commands in text form
seq              =  1*19DIGIT                ; Sequence number, 1 to 19 digits integer in decimal form
args             =  1*35(SP / VCHAR)         ; Argument(s), 1 to 35 printable characters plus space
cmd-message      =  seq SP cmd [SP args]     ; Command Message format

```

#### Acknowlegdement message format
```ABNF
DIGIT            =  %x30-39
ack-message      =  1*19DIGIT ; Sequence number, 1 to 19 digits integer in decimal form

```
  
#### Advertisement message format
```ABNF
DIGIT            =  %x30-39
SP               =  %x20
VCHAR            =  %x21-7E                  ; Printable characters
timestamp        =  1*19DIGIT                ; Timestamp, preferably of form YYYYMMDDhhmmss[fff]
type             =  4VCHAR                   ; Advertisement type
args             =  1*35(SP / VCHAR)         ; Argument(s), 1 to 35 printable characters plus space

```
  
#### Security considerations
Message Integrity Protection is not considered for this underlaying protocol. If integrity is required, it SHALL be provided by an underlaying protocol (for example, TLS or IPSec, with NULL encryption if mandated by your local regulation). 

The MQTT message broker SHOULD be set up to enforce authentication and access control. 

Basic roles are suggested as follow:
  - The agent role SHOULD enable subscription to `repeaters/<callsign>/v1` and let an agent publish to `repeaters/<callsign>/v1/response` and `repeaters/<callsign>/v1/advertise.
  - The control client role SHOULD enable subscription to `repeaters/+/v1/response` and `repeaters/+/v1/advertise` and let a control client post on `repeaters/+/v1`. More granular roles MAY be implemented to fine tune access rules to repeater administrators. 

### RRCP over LoRaWAN
Use of this control channel is provided as a last resort solution, in case your repeater is not in reach of other infrastructure. 

The controlled device MUST support **at least** class B operation.

  - **Commands** SHALL be sent on **port 1**.
  - **Acknowledgements** SHALL be sent on **port 1**.
  - **Advertisements** SHALL be sent on **port 2**.

#### Message format
A RRCP over APRS message is composed as the concatenation of the following:
  - A 1 byte **Control** (CTL) field, which represents the requested command. Value of control word is defined for each command.
  - A variable size **Arguments** (ARG) field.
    - It contains the arguments required by specific commands.
    - Its size MUST be between 0 and 35 bytes.
    - If applicable, multiple arguments are separated by the character 0x20.
    - Each argument byte's value MUST be more than, or equal to, 0x20, and less than, or equal to, 0x7E.

This format constitutes the payload of a LoRaWAN packet regardless of its nature (command, reply, advertisement). 

### RRCP over APRS
Due to the nature of APRS messages (lack of integrity protection, lack of replay resistance), a message integrity tag is appended to each message. 

#### Message format
A RRCP over APRS message is composed as the concatenation of the following:
  - A 3 bytes **Header** of fixed value "RC!"
  - A 6 bytes **Message Sequence Number** (SEQ) field. 
    - Its content is the base64-encoded representation of a 32 bits monotonic unsigned integer sequence counter. 
    - The value of SEQ must be used at most once over the air for a given session key. 
    - The trailing '==' of the base64 value MUST be stripped during encapsulation, and MUST be appended locally during decapsulation.
    - A new session key MUST be negociated once the counter overflows, or if the counter needs to be reset to 0.
    - Replay protection SHALL be enforced by the message broker and the agent. To do this, they MUST keep track of the last valid sequence number, and SHALL discard any message whose sequence number is less or equal to that last valid sequence number even if the Message Integrity Tag is valid against the session key.
  - A 1 byte **Control** (CTL) field, which represents the requested command. Value of control word is defined for each command.
  - A variable size **Arguments** (ARG) field.
    - It contains the arguments required by specific commands.
    - Its size MUST be between 0 and 35 bytes.
    - If applicable, multiple arguments are separated by the character 0x20.
    - Each argument byte's value MUST be more than, or equal to, 0x20, and less than, or equal to, 0x7E.
  - A 22 bytes **Message Integrity Check** (MIC) field. 
    - Its content is the base64-encoded representation of a 128 bits message integrity tag. 
    - The trailing '==' of the base64 value MUST be stripped during encapsulation, and MUST be appended locally during decapsulation.
    - The 128 bits message integrity tag is the result of computing the AES-CMAC value of the preceding fields. 
    - The SEQ field is encoded in its 6 bytes base64 form prior to performing this operation.
  
This format constitutes the payload of an APRS packet regardless of its nature (command, reply, advertisement). 

## Commands

The following table describes the format of commands that can be sent by a control client.

| Command                  | Control Field value | Text form    | Argument(s)    |
| ------------------------ | ------------------- | ------------ | -------------- |
| Ping                                    | 0x30 | ping         | *No Argument*  |
| Change Module                           | 0x31 | chmod        | new module     |
| Disconnect repeater from current module | 0x32 | disc         | *No Argument*  |
| Enable RF                               | 0x33 | txon         | *No Argument*  |
| Disable RF                              | 0x34 | txoff        | *No Argument*  |
| Reboot controlled device                | 0x35 | reboot       | *No Argument*  |
| Request status                          | 0x36 | getstatus    | *No Argument*  |
| Join Request (APRS specific)            | 0x40 | *N.A.*       | Encrypted session key, beaconing interval |
| Join Reply (APRS specific)              | 0x41 | *N.A.*       | *No Argument*  |
| Over the Air Credentials Update         | 0x42 | otacu        | type, New value (encrypted if applicable) |
| Check credentials                       | 0x43 | ckc          | type, challenge if applicable |
| Switch credentials                      | 0x44 | swc          | *No Argument*  |
| Run Provisioning                        | 0x45 | provision    | Source Url     |
| Update agent                            | 0x46 | update       | Source Url     |
| Start generator                         | 0x50 | genstart     | *No Argument*  |
| Stop generator                          | 0x51 | genstop      | *No Argument*  |

### Ping

### Change Module

### Disconnect repeater from current module

### Enable RF

### Disable RF

### Reboot controlled device

### Over the Air Credentials update

### Switch credentials

### Run Provisioning

### Update agent

### Join Request (APRS specific)

### Join Reply (APRS specific)

## Baseline Support Profile

Support for the following commands MUST be implemented by all implementations of the protocol.
  - Ping
  - Enable controlled device
  - Disable controlled device
  - Reboot controlled device

Support of other command is OPTIONAL, and at the controlled device implementer's discretion.
  
## Replies, Advertisements
  
The following table describes the format of responses and advertisements that can be sent by an agent.

| Reply / Advertisement                   | Control Field value | Text form |  Argument(s)     |
| --------------------------------------- | ------------------- | --------- | ---------------- |
| Acknowledgement *(response)*            | 0x20                | *(empty)* | Acknowledged Command Sequence number |
| Advertise presence *(advertisement)*    | 0x21                | 'ADVT'    | Timestamp, Power status, Device Serial Number, beaconing interval |
| Report breaker trip *(advertisement)*   | 0x22                | 'TRIP'    | Timestamp, Breaker ID  |
| Generator status *(advertisement)*      | 0x23                | 'GENS'    | Timestamp, fuel percentage, gen started?, gen lockout?, gen (temp\|fault code)  |
