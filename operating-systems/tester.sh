#!/bin/bash

set -e  # αν κάτι αποτύχει, σταματάει το script

echo "🧹 Cleaning previous shared memory..."
./destroy 2>/dev/null || true
sleep 1

echo "🚀 TEST 1 – 2 διεργασίες σε έναν διάλογο"

# -------- TEST 1: A & B στον ίδιο διάλογο --------
# A: δημιουργεί διάλογο 1, στέλνει 2 μηνύματα, TERMINATE, έξοδος
cat <<EOF > inA1
1
1
hello from A
1
second from A
2
3
EOF

# B: join στον διάλογο 1, περιμένει λίγο (receiver thread), έξοδος
cat <<EOF > inB1
2
1
3
EOF

./test < inA1 > outA1 &
PA=$!
sleep 0.3
./test < inB1 > outB1 &
PB=$!

wait $PA $PB

echo ""
echo "========= OUTPUT A1 ========="
cat outA1
echo ""
echo "========= OUTPUT B1 ========="
cat outB1

echo ""
echo "🚀 TEST 2 – 3 διεργασίες στον ίδιο διάλογο"

# -------- TEST 2: A, B, C στον ίδιο διάλογο --------
./destroy 2>/dev/null || true
sleep 1

cat <<EOF > inA2
1
1
msg1
1
msg2
2
3
EOF

cat <<EOF > inB2
2
1
3
EOF

cat <<EOF > inC2
2
1
3
EOF

./test < inA2 > outA2 &
PA=$!
sleep 0.3
./test < inB2 > outB2 &
PB=$!
sleep 0.3
./test < inC2 > outC2 &
PC=$!

wait $PA $PB $PC

echo ""
echo "========= OUTPUT A2 ========="
cat outA2
echo ""
echo "========= OUTPUT B2 ========="
cat outB2
echo ""
echo "========= OUTPUT C2 ========="
cat outC2

echo ""
echo "🚀 TEST 3 – Δεύτερος διάλογος (ID 2)"

# -------- TEST 3: Δεύτερος ανεξάρτητος διάλογος --------
./destroy 2>/dev/null || true
sleep 1

cat <<EOF > inA3
1
1
hello D1
2
3
EOF

# E: δημιουργεί δεύτερο διάλογο
cat <<EOF > inE3
1
3
EOF

./test < inA3 > outA3 &
PA=$!
sleep 0.3
./test < inE3 > outE3 &
PE=$!

wait $PA $PE

echo ""
echo "========= OUTPUT A3 ========="
cat outA3
echo ""
echo "========= OUTPUT E3 ========="
cat outE3

echo ""
echo "✅ ΟΛΑ ΤΑ TEST ΟΛΟΚΛΗΡΩΘΗΚΑΝ – ΔΕΝ ΥΠΗΡΞΕ ΚΟΛΛΗΜΑ"
echo "   Έλεγξε τα outA*/outB*/outC*/outE* για το περιεχόμενο."