To check if **port 80** is open for both inward and outward communication through your firewall on your Linux system, you can follow these steps:

### 1. **Check Firewall Rules with `ufw` (Uncomplicated Firewall)**
If your system is using `ufw` as a firewall management tool (common on Ubuntu), you can check if port 80 is open with the following commands:

- **Check the status of `ufw`**:

  ```bash
  sudo ufw status
  ```

  This will display a list of the ports and services that are allowed or denied. Look for port `80` (HTTP) in the output. If it is listed as "ALLOW," it means it's open for inward communication.

- **Allow Port 80 if needed**:

  If you find that port 80 is not open, you can open it with the following command:

  ```bash
  sudo ufw allow 80/tcp
  ```

- **Check if port 80 is open for outward communication**:

  By default, `ufw` allows all outgoing traffic unless explicitly blocked. To check if outgoing connections on port 80 are blocked, you can inspect the rules:

  ```bash
  sudo ufw status verbose
  ```

  Look under the "Outgoing" section to see if there are any rules that block outbound communication.

### 2. **Check Firewall Rules with `iptables`**
If you're using `iptables` for firewall rules (or `nftables`), you can check if port 80 is blocked or open by listing the firewall rules.

- **Check existing rules**:

  ```bash
  sudo iptables -L -v -n
  ```

  This command will display the current rules. Look for rules that either **accept** or **deny** traffic on port `80`. You should check both `INPUT` (inward communication) and `OUTPUT` (outward communication) chains.

- **Allow inbound traffic on port 80**:

  If you need to allow incoming traffic on port 80, you can add the following rule:

  ```bash
  sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
  ```

- **Allow outbound traffic on port 80**:

  To allow outbound communication, you can add this rule:

  ```bash
  sudo iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
  ```

### 3. **Test Port 80 Using `nc` (Netcat)**
To check if port 80 is open and listening, you can test it with `nc`:

- **Test incoming traffic**:

  Run this command to test if port 80 is open for incoming traffic:

  ```bash
  nc -zv 0.0.0.0 80
  ```

  If port 80 is open, you will see a message indicating that it is connected. If it’s blocked, you’ll see a connection refused or timed out message.

- **Test outgoing traffic**:

  You can try connecting to an external server on port 80 to verify that outbound traffic is allowed:

  ```bash
  nc -zv google.com 80
  ```

  If the connection is successful, it indicates that outbound traffic on port 80 is allowed.

### 4. **Using `nmap` to Check Port 80**
You can also use `nmap` to scan port 80 and see if it's open:

```bash
sudo nmap -p 80 localhost
```

This will show if port 80 is open and accepting inbound connections on your local machine. If you want to test outgoing connections, you can use `nmap` to check a remote server (like `google.com`):

```bash
sudo nmap -p 80 google.com
```

### Summary
- Use `ufw status` or `iptables -L` to check if there are any firewall rules blocking port 80.
- You can allow port 80 traffic with `ufw allow 80/tcp` or `iptables -A INPUT -p tcp --dport 80 -j ACCEPT`.
- Use `nc` or `nmap` to test if port 80 is open and accepting connections.

This will help you determine whether port 80 is open or blocked on your system.