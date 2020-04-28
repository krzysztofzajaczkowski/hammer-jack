from Client import Client


def main():
    username = input("Username: ")
    client = Client(username, "localhost", 63300)
    if client.connect() == 0:
        client.join_queue()


if __name__ == "__main__":
    main()