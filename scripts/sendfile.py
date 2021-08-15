import os
import sys
import pickle
import argparse
import ipaddress
import socket
import time
from pathlib import Path


ServerPort = 8089

def recvStr(sock):
    data = sock.recv(4)
    numBytes = int.from_bytes(data, "big")
    data = sock.recv(numBytes)
    return data.decode("utf-8")


def sendStr(sock, s):
    data = s.encode("utf-8")
    sent = sock.send(len(data).to_bytes(4, "big"))
    assert sent == 4
    sent = sock.send(data)
    assert sent == len(data)


def sendFile(sock, filePath):
    ''' Send a big file over socket. Should pair with function recvFile '''
    if not sock:
        raise socket.error
    length = filePath.stat().st_size
    sentByteNum = sock.send(length.to_bytes(4, "big"))
    assert sentByteNum == 4
    chunckSize = 64 * 1024
    totalSent = 0
    lastProcess = 0
    startTime = time.perf_counter()
    lastTime = startTime
    lastSent = 0
    with filePath.open("rb") as f:
        while True:
            data = f.read(chunckSize)  # Send a small chunk of files
            if not data:
                break
            sendByteNum = sock.send(data)
            assert sendByteNum == len(data)
            totalSent += sendByteNum
            progress = int(totalSent/length * 20)
            if progress > lastProcess:
                curTime = time.perf_counter()
                deltaTime = curTime - lastTime
                deltaSent = totalSent - lastSent
                speed = deltaSent / deltaTime / 1024
                lastSent = totalSent
                lastTime = curTime
                lastProcess = progress

                sys.stdout.write('\r')
                # the exact output you're looking for:
                sys.stdout.write("[%-20s] %3d%% %.0f KB/s" % ('='*progress, 5*progress, speed))
                sys.stdout.flush()
    deltaTime = curTime - startTime
    aveSpeed = length / deltaTime / 1024
    print("\nCost time %.1fs, average speed %.0f KB/s" % (deltaTime, aveSpeed))


def pickOneHost(hostDict):
    hostIp = None
    phoneChecked = False
    while hostDict:
        ipList = list(hostDict.keys())
        if len(hostDict) > 1:
            print("There're %d previous ip scan results:" % len(hostDict))
            for i, ip in enumerate(ipList):
                print("(%d) %s %s" % (i, ip, hostDict[ip]))
            key = input("Please choose one to try:")
            try:
                idx = int(key)
                ip = ipList[idx]
            except Exception:
                return None
        else:
            ip = ipList[0]

        # Try to connect
        while True:
            s = socket.socket()
            try:
                s.connect((ip, ServerPort))
                sendStr(s, "Identify yourself")
                recvStr(s)
                hostIp = ip
                break
            except Exception:
                if not phoneChecked:
                    print("Cannot connect %s %s. Please make sure the phone app is turned on." % (ip, hostDict[ip]))
                    input("Press enter to continue...")
                    phoneChecked = True
                else:
                    break
            finally:
                s.close()

        if not hostIp:
            print("Removed %s %s from scan result" % (ip, hostDict[ip]))
            hostDict.pop(ip)
        else:
            break

    return hostIp


def main(argv):
    # Parse the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-network", help="The ip network to scan", default="192.168.0.0/255.255.255.0")
    parser.add_argument("-ip", help="The ip address to send file")
    parser.add_argument("file", help="file to send")

    args = parser.parse_args(argv)
    filePath = Path(args.file)
    if not filePath.is_file():
        print("local file %s doesn't exist" % str(filePath))
        return 1

    hostDict = dict()  # Element (ip, hostName)
    cachePath = Path(os.path.expanduser('~'))/"ipScanCache.pickle"
    if cachePath.is_file():
        with cachePath.open("rb") as f:
            hostDict = pickle.load(f)

    if args.ip:
        s = socket.socket()
        try:
            s.connect((args.ip, ServerPort))
            sendStr(s, "Identify yourself")
            msg = recvStr(s)
            if not msg.startswith("This is a file receiver at"):
                return 1
            hostName = msg.split("This is a file receiver at")[1].strip()
            hostDict[args.ip] = hostName
        except Exception:
            print("Cannot connect %s" % args.ip)
            return 1
        finally:
            s.close()

    ip = pickOneHost(hostDict)

    if not ip:
        # Cannot connect with previous scan result. Need a new scan
        for addr in ipaddress.IPv4Network(args.network):
            s = socket.socket()
            s.settimeout(0.2)
            try:
                print("Scan %s" % str(addr))
                s.connect((str(addr), ServerPort))
                s.settimeout(1)
                sendStr(s, "Identify yourself")
                msg = recvStr(s)
                if not msg.startswith("This is a file receiver at"):
                    s.close()
                    continue
                hostName = msg.split("This is a file receiver at")[1]
                hostDict[str(addr)] = hostName
                print("Found host %s" % hostName)
            except Exception:
                pass
            s.close()
        if not hostDict:
            print("Cannot find any device in the range %s" % args.network)
            return 1
        ip = pickOneHost(hostDict)
        assert ip
    # Save the hostDict
    with cachePath.open("wb") as f:
        pickle.dump(hostDict, f)

    s = socket.socket()
    try:
        s.connect((ip, ServerPort))
        sendStr(s, "Please download file")
        msg = recvStr(s)
        if msg != "What's the file name?":
            return 1
        sendStr(s, filePath.name)
        print("Sending file to %s %s..." % (ip, hostDict[ip]))
        sendFile(s, filePath)
        msg = recvStr(s)
        if msg != "File received":
            return 1
        print("Sent file %s" % str(filePath))
    except Exception as e:
        print("Something wrong happend during transfering file")
        print(e)
    s.close()


if __name__ == "__main__":
    main(sys.argv[1:])
