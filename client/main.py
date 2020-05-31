from Client import Client


def join_queue(username):
    client = Client(username)
    if client.connect() != -1:
        client.join_queue()


def ask_username():
    username = input("Username: ")
    return username


def main():
    username = ask_username()
    join_queue(username)


if __name__ == "__main__":
    main()