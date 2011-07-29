extiface="eth0"
serveriface="ppp0"

echo "Killing network manager"
/etc/init.d/network-manager stop

echo "Setting up default iptables policy"
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

echo "Setting ip masquerading for $extiface"
iptables -t nat -A POSTROUTING -o $extiface -j MASQUERADE

echo "Setting ip masquerading for $serveriface"
iptables -t nat -A POSTROUTING -o $serveriface -j MASQUERADE

echo "Enabling IP forwarding"
echo 1 > /proc/sys/net/ipv4/ip_forward

echo "WARNING! Make sure your DNS resolver is correct. I am helpfully catting it for you now."
cat /etc/resolv.conf
