#!/usr/bin/env python3

import hashlib
import ipaddress
import os
import socket
import sys
from typing import Any, Callable, Dict, List


CHUNK_SIZE = 16
ICMP_DATA_OFFSET = 24
IP_HEADER_OFFSET = 20
IS_NT = os.name == 'nt'
NULL_BYTE = b'\0'
PCKT_SIZE = 84


MAGIC = {
    'mst': b'PYNGMETASTART',
    'men': b'PYNGMETAEND',
    'dst': b'PYNGDATASTART',
    'den': b'PYNGDATAEND',
}


ERRORS = {
    'INVALID_IPV4': '[!]  Invalid IPv4 address: {}',
    'PERMISSIONS': '[!]  Pyng server requires root level permissions',
    'BIND': '[!]  Failed to bind on {}: {}'
}


REPORTS = {
    'LISTENING': 'Pyng server listening on {}',
    'TRANSFER_START': 'T{}: Start transfer from {}'
}


def batch_report(messages: List[str], prefix: str = '[*] ') -> None:
    for m in messages:
        report(m, prefix)


def report(message: str, prefix: str = '[*] ') -> None:
    print(f'{prefix}{message}')


def crtlc_wrapper(func: Callable[..., Any], params: List[Any] = []) -> None:
    try:
        func() if not len(params) else func(*params)
    except KeyboardInterrupt:
        sys.exit()


def clean_list(array: List[bytes], remove: List[bytes]) -> List[bytes]:
    return [el for el in array if el.rstrip(NULL_BYTE) not in remove]


def parser(message: List[bytes]) -> Dict[str, bytes]:
    data_start_index = message.index(MAGIC['dst'])
    magic = list(MAGIC.values())
    return {
        'meta': b''.join(clean_list(message[:data_start_index], magic)),
        'data': b''.join(clean_list(message[data_start_index:], magic))
    }


def handler(src: str, buffer: List[bytes], transfer: int) -> None:

    clean_dict = parser(buffer)

    file_name = f'./pyng_{src}_{transfer}'

    # TODO : ERROR WRAPPERS
    with open(file_name, 'wb') as f:
        f.write(clean_dict['data'])

    batch_report([
        'Complete',
        f'Remote:\t{clean_dict["meta"].decode()}',
        f'Local:\t{file_name}',
        f'Size:\t{len(clean_dict["data"])}',
        f'MD5:\t{hashlib.md5(clean_dict["data"]).hexdigest()}\n'
    ], f'T{transfer}: ')


def main() -> None:

    try:
        host = '0.0.0.0' if len(sys.argv) == 1 else sys.argv[1]
        ipaddress.IPv4Address(host)
    except ValueError:
        sys.exit(ERRORS['INVALID_IPV4'].format(host))

    try:
        srv = socket.socket(
            socket.AF_INET,
            socket.SOCK_RAW,
            socket.IPPROTO_IP if IS_NT else socket.IPPROTO_ICMP
        )
        srv.bind((host, 0))
    except PermissionError:
        sys.exit(ERRORS['PERMISSIONS'])
    except OSError as e:
        sys.exit(ERRORS['BIND'].format(host, e))

    report(REPORTS['LISTENING'].format(host))

    buffer: List[bytes] = []
    client_active = False
    transfer_number = 1

    while True:

        pckt, src = srv.recvfrom(PCKT_SIZE)
        chunk = pckt[IP_HEADER_OFFSET:][ICMP_DATA_OFFSET:][:CHUNK_SIZE]

        if MAGIC['mst'] in chunk:
            report(REPORTS['TRANSFER_START'].format(transfer_number, src[0]))
            client_active = True

        if client_active:
            buffer.append(chunk.rstrip(NULL_BYTE))

        if MAGIC['den'] in chunk:
            client_active = False
            handler(src[0], buffer, transfer_number)
            transfer_number += 1
            buffer.clear()


if __name__ == '__main__':
    crtlc_wrapper(main)
