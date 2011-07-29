bridgeiface=eth0
hostonlyiface=eth2
vpniface=ppp0
vpnifacetwo=ppp1

echo "Setting ip masquerading for BRIDGED Interface"
iptables -t nat -A POSTROUTING -o $bridgeiface -j MASQUERADE


echo "Performing MITM on $hostonlyiface"
iptables -t nat -A PREROUTING -j REDIRECT -i $hostonlyiface -p tcp -m tcp --to-ports 20755
iptables -t nat -A PREROUTING -j REDIRECT -i $hostonlyiface -p udp -m udp --to-ports 20755

echo "Performing MITM on $vpniface"
iptables -t nat -A PREROUTING -j REDIRECT -i $vpniface -p tcp -m tcp --to-ports 20755
iptables -t nat -A PREROUTING -j REDIRECT -i $vpniface -p udp -m udp --to-ports 20755

echo "Performing MITM on $vpnifacetwo"
iptables -t nat -A PREROUTING -j REDIRECT -i $vpnifacetwo -p tcp -m tcp --to-ports 20755
iptables -t nat -A PREROUTING -j REDIRECT -i $vpnifacetwo -p udp -m udp --to-ports 20755
