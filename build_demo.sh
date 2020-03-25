ROOTKIT=rootkit_demo
PRIVATE=private
PUBLIC=public
SOURCE=source
PYTHON=python

mkdir $ROOTKIT
touch $ROOTKIT/process

mkdir $ROOTKIT/$PRIVATE
touch $ROOTKIT/$PRIVATE/full_peer_list

mkdir $ROOTKIT/$PUBLIC
touch $ROOTKIT/$PUBLIC/peer_list
mkdir $ROOTKIT/$PUBLIC/$SOURCE
cp -r $PYTHON/botnet_p2p $ROOTKIT/$PUBLIC/$SOURCE
cp $PYTHON/server.py $ROOTKIT/$PUBLIC/$SOURCE

python3 $PYTHON/generate_rsa_keys.py
mv private_key $ROOTKIT/$PRIVATE
mv public_key $ROOTKIT/$PUBLIC/$SOURCE

