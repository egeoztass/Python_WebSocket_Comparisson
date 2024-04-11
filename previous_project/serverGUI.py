import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import traceback


class DiSUcordServer:
    def __init__(self, host='0.0.0.0'):  # initialize the server. 0.0.0.0 is for all available interfaces.
        self.gui = None
        self.host = host
        self.port = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.channels = {"IF 100": set(), "SPS 101": set()}
        self.is_running = False
        self.threads = []

    def set_port(self, port):  # sets the port number for the server to listen on.
        self.port = port

    def set_gui(self, gui):  # associates a GUI object with the server for updating GUI elements.
        self.gui = gui

    def start(self):  # starts the server, making it listen for incoming connections.
        if self.port is None:
            self.log("Error: Port number not set.")
            raise ValueError("Port number not set.")
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.is_running = True
        self.log(f"Server started on {self.host}:{self.port}")

        try:
            while self.is_running:   # run a loop to accept new connections.
                try:
                    conn, addr = self.server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.start()  # start a thread for each client.
                    self.threads.append(thread)
                except socket.timeout:
                    pass
                except Exception as e:
                    if not self.is_running:
                        break
        finally:
            self.cleanup()

    def stop(self):  # stop the server
        self.is_running = False
        self.notify_all_clients("Server is shutting down.")  # notify all clients about shutting down.
        # stop listening for new connections!
        for _, client_conn in list(self.clients.items()):
            try:
                if client_conn.fileno() != -1:
                    client_conn.shutdown(socket.SHUT_RDWR)
                client_conn.close()
            except Exception as e:
                self.log(f"Error closing client connection: {e}")

        if self.server_socket:
            self.server_socket.close()

        for t in self.threads:
            t.join(timeout=1)

        self.log("Server stopped.")

    def cleanup(self):  # closes all client connections and closes server socket.
        for _, conn in self.clients.items():
            try:
                conn.close()
            except Exception as e:
                self.log(f"Error closing client connection: {traceback.format_exc()}")
        self.server_socket.close()
        for thread in self.threads:  # wait for all threads to finish.
            thread.join()

    def handle_client(self, conn, addr):  # manages communication with a single client.
        username = None
        try:
            username = conn.recv(1024).decode('utf-8')
            if not username:
                conn.close()
                return

            if username in self.clients:  # for duplicate usernames.
                conn.send("Username already in use. Please try a different username.".encode('utf-8'))
            else:
                self.clients[username] = conn
                self.log(f"{username} connected from {addr}")
                self.update_client_lists()

            while self.is_running:
                try:
                    message = conn.recv(1024).decode('utf-8')
                    if not message:
                        break

                    if message.startswith("subscribe:"):  # handle subscriptions
                        self.handle_subscribe(username, message, conn)
                    elif message.startswith("unsubscribe:"):  # handle unsubscriptions
                        self.handle_unsubscribe(username, message, conn)
                    elif ":" in message:
                        self.handle_channel_message(username, message)
                    else:
                        break
                except socket.error as e:  # error handling
                    if not self.is_running:
                        break
                    self.log(f"Socket error with {username}: {e}")
                    break
                except Exception as e:
                    self.log(f"Unexpected error with {username}: {e}")
                    break
        finally:
            self.cleanup_client(username, conn)

        self.log(f"Connection with {username} closed")

    def handle_subscribe(self, username, message, conn):  # process subscription requests
        channel = message.split(":")[1]
        if username in self.channels[channel]:  # if already subscribed
            self.log(f"{username} is already subscribed to {channel}")
            conn.send(f"Already subscribed to {channel}".encode('utf-8'))
        else:
            self.channels[channel].add(username)
            self.log(f"{username} subscribed to {channel}")
            conn.send(f"Subscribed to {channel}".encode('utf-8'))
        self.update_client_lists()

    def handle_unsubscribe(self, username, message, conn):  # handle unsubscriptions
        channel = message.split(":")[1]
        if username in self.channels[channel]:
            self.channels[channel].discard(username)
            self.log(f"{username} unsubscribed from {channel}")
            conn.send(f"Unsubscribed from {channel}".encode('utf-8'))
        self.update_client_lists()

    def handle_channel_message(self, username, message):  # process messages send to a channel
        try:
            channel, msg = message.split(':', 1)
            if channel in self.channels and username in self.channels[channel]:
                # Log the message being handled
                self.log(f"Handling message from {username} to {channel}: {msg}")

                # Construct the message to be sent to other clients
                formatted_message = f"{username} to {channel}: {msg}"
                # Send the message to all subscribed clients except the sender
                for subscriber in self.channels[channel]:
                    if subscriber != username:  # Exclude the sender
                        client_conn = self.clients.get(subscriber)
                        if client_conn:
                            self.log(f"Sending message to {subscriber}")  # Log who we're sending the message to
                            client_conn.send(formatted_message.encode('utf-8'))
                # Send a confirmation to the sender
                sender_conn = self.clients.get(username)
                if sender_conn:
                    self.log(f"Confirming message to sender {username}")  # Log the confirmation
                    sender_conn.send(f"from you to {channel}: {msg}".encode('utf-8'))
        except Exception as e:
            self.log(f"Error handling message: {e}")

    def cleanup_client(self, username, conn):  # remove a client from server's records
        if username and username in self.clients:
            del self.clients[username]
            for channel in self.channels:
                self.channels[channel].discard(username)
            self.log(f"{username} has disconnected.")
            self.update_client_lists()
        conn.close()  # close that clients connection

    def multicast_message(self, message, channel):  # send a message to all subscribed channel users, with specified channel
        for user in list(self.channels[channel]):  # Convert to list to avoid modifying the set during iteration
            client_conn = self.clients.get(user)
            if client_conn:
                try:
                    client_conn.send(message.encode('utf-8'))
                except (BrokenPipeError, ConnectionError) as e:
                    # Handle the error, e.g., log it, remove the client, or take appropriate action
                    self.log(f"Error sending message to {user}: {e}")
                    self.clients.pop(user, None)
                    self.channels[channel].discard(user)
            else:
                # Handle the case where the client is not found in self.clients
                self.log(f"Client {user} not found in clients")

    def notify_all(self, message):  # send a message to all connected clients
        for client_conn in self.clients.values():
            try:
                client_conn.send(message.encode('utf-8'))
            except Exception as e:
                self.log(f"Error sending notification: {e}")

    def notify_all_clients(self, message):  # notifies all clients about server-wide events or messages.
        for _, client_conn in list(self.clients.items()):
            try:
                client_conn.send(message.encode('utf-8'))
            except Exception as e:
                self.log(f"Error notifying client: {e}")

    def set_log_callback(self, callback):  # sets a callback function for logging messages.
        self.log_callback = callback

    def log(self, message):  # logs messages either through the GUI or to the console.
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def update_client_lists(self):  # updates the GUI with the latest client and subscriber lists.
        if self.gui:
            self.gui.update_connected_clients(list(self.clients.keys()))
            self.gui.update_if100_subscribers(list(self.channels["IF 100"]))
            self.gui.update_sps101_subscribers(list(self.channels["SPS 101"]))


class ServerGUI:
    def __init__(self, master):  # initialize the ServerGUI.
        self.master = master
        master.title("DiSUcord Server")
        master.geometry("600x700")

        control_frame = tk.Frame(master)
        control_frame.grid(row=0, column=0, sticky="ew")

        tk.Label(control_frame, text="Server Port:").grid(row=0, column=0)
        self.port_entry = tk.Entry(control_frame)
        self.port_entry.grid(row=0, column=1)
        self.port_entry.insert(0, "12345")

        self.start_button = tk.Button(control_frame, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=2)

        self.stop_button = tk.Button(control_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3)

        self.log = scrolledtext.ScrolledText(master, state='disabled')
        self.log.grid(row=1, column=0, sticky="nsew")

         # Label and Text Box for Connected Users
        tk.Label(master, text="Connected Users").grid(row=2, column=0, sticky="w")
        self.connected_clients_box = scrolledtext.ScrolledText(master, height=6, state='disabled')
        self.connected_clients_box.grid(row=3, column=0, sticky="nsew")

        # Label and Text Box for IF100 Subscribers
        tk.Label(master, text="IF100 Subscribers").grid(row=4, column=0, sticky="w")
        self.if100_subscribers_box = scrolledtext.ScrolledText(master, height=6, state='disabled')
        self.if100_subscribers_box.grid(row=5, column=0, sticky="nsew")

        # Label and Text Box for SPS101 Subscribers
        tk.Label(master, text="SPS101 Subscribers").grid(row=6, column=0, sticky="w")
        self.sps101_subscribers_box = scrolledtext.ScrolledText(master, height=6, state='disabled')
        self.sps101_subscribers_box.grid(row=7, column=0, sticky="nsew")

        self.server = DiSUcordServer()
        self.server_thread = None

        master.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_server(self):  # start server
        try:
            port = int(self.port_entry.get())  # extracts the port number from the GUI
        except ValueError:
            messagebox.showerror("Error", "Invalid port number!")
            return

        self.server = DiSUcordServer()  # Reinitialize the server
        self.server.set_port(port)   # initializes the server with this port
        self.server.set_log_callback(self.update_log)
        self.server.set_gui(self)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.start()  # starts a new thread to run the server
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_server(self):  # stops the server when the stop button is clicked.
        # Call the server's stop method
        if self.server:
            self.server.stop()

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("Server stopped.")

    def update_log(self, message):  # updates the log text box with new messages.
        self.log.config(state='normal')
        self.log.insert(tk.END, message + "\n")
        self.log.config(state='disabled')

    def update_connected_clients(self, client_list):   # updates the GUI with the list of currently connected clients.
        def update():
            self.connected_clients_box.config(state='normal')
            self.connected_clients_box.delete(1.0, tk.END)
            self.connected_clients_box.insert(tk.END, "\n".join(client_list))
            self.connected_clients_box.config(state='disabled')

        self.master.after(0, update)

    def update_if100_subscribers(self, subscriber_list):  # updates the GUI with the list of subscribers to the IF100 channel.
        def update():
            self.if100_subscribers_box.config(state='normal')
            self.if100_subscribers_box.delete(1.0, tk.END)
            self.if100_subscribers_box.insert(tk.END, "\n".join(subscriber_list))
            self.if100_subscribers_box.config(state='disabled')

        self.master.after(0, update)

    def update_sps101_subscribers(self, subscriber_list):  # updates the GUI with the list of subscribers to the SPS101 channel.
        def update():
            self.sps101_subscribers_box.config(state='normal')
            self.sps101_subscribers_box.delete(1.0, tk.END)
            self.sps101_subscribers_box.insert(tk.END, "\n".join(subscriber_list))
            self.sps101_subscribers_box.config(state='disabled')

        self.master.after(0, update)

    def on_close(self):
        # Stop the server if it is running
        if self.server and self.server.is_running:
            self.stop_server()

        # Explicitly destroy the GUI window
        self.master.destroy()


root = tk.Tk()
gui = ServerGUI(root)
root.mainloop()
