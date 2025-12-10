#ifndef BPLUS_DATANODE_H
#define BPLUS_DATANODE_H

#include "record.h"

// Απλός κόμβος δεδομένων (leaf node) του B+ Tree
typedef struct {
    int is_leaf;          // 1 αν είναι φύλλο, αλλιώς 0
    int next_block;       // block number του επόμενου leaf node (ή -1)
    int key_count;        // πόσες εγγραφές περιέχει
    Record records[4];    // 4 εγγραφές ανά κόμβο (512 bytes block size)
} BPlusDataNode;

#endif
