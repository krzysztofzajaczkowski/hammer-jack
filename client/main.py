from Client import Client


def main():
    username = input("Username: ")
    client = Client(username)
    client.connect()
    client.join_queue()


if __name__ == "__main__":
    main()