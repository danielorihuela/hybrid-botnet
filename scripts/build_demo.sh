GITSOURCE=src
OUTPUT=demo
ROOTKIT=rootkit_demo
PRIVATE=private
PUBLIC=public
SOURCE=source
BOTNET=botnet
HTTP=http

rm $OUTPUT -r

mkdir $OUTPUT
mkdir $OUTPUT/$ROOTKIT
touch $OUTPUT/$ROOTKIT/process

mkdir $OUTPUT/$ROOTKIT/$PRIVATE
touch $OUTPUT/$ROOTKIT/$PRIVATE/full_peer_list

mkdir $OUTPUT/$ROOTKIT/$PUBLIC
touch $OUTPUT/$ROOTKIT/$PUBLIC/peer_list
mkdir $OUTPUT/$ROOTKIT/$PUBLIC/$SOURCE
cp -r $GITSOURCE/$BOTNET/botnet_hybrid $OUTPUT/$ROOTKIT/$PUBLIC/$SOURCE
cp $GITSOURCE/$BOTNET/server.py $OUTPUT/$ROOTKIT/$PUBLIC/$SOURCE
mkdir $OUTPUT/$ROOTKIT/$PUBLIC/$HTTP
cp $GITSOURCE/$HTTP/* $OUTPUT/$ROOTKIT/$PUBLIC/$HTTP

python3 $GITSOURCE/$BOTNET/generate_rsa_keys.py
mv private_key $OUTPUT
mv public_key $OUTPUT/$ROOTKIT/$PUBLIC/$SOURCE

