from Client import Client


def main():
    username = input("Username: ")
    client = Client(username)
    if client.connect() != -1:
        client.join_queue()


if __name__ == "__main__":
    main()