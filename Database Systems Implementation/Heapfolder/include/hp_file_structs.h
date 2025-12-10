#ifndef HP_FILE_STRUCTS_H
#define HP_FILE_STRUCTS_H

#include <record.h>

/**
 * @file hp_file_structs.h
 * @brief Data structures for heap file management
 */

/* -------------------------------------------------------------------------- */
/*                              Data Structures                               */
/* -------------------------------------------------------------------------- */

/**
 * @brief Heap file header containing metadata about the file organization
 */
typedef struct HeapFileHeader {
    int is_heap_file; // 1 = true, 0 = false
    int last_data_block; // ο αριθμος του τελευταιου block που περιεχει δεδομενα
    int total_records; // συνολικος αριθμος εγγραφων στο αρχειο
    int records_per_block; // ποσες εγγραφες χωραει ενα block
} HeapFileHeader;

/**
 * @brief Iterator for scanning through records in a heap file
 */
typedef struct HeapFileIterator{
    int file_handle; //αριθμος αναφορας 
    HeapFileHeader* header; //πληροφοριες για τη δομη του αρχειου 

    int search_id;  // αν id == -1 διαβαζει ολες τις εγγραφες αλλιως record.id == search_id
    int current_block; //που ειμαστε και start from block 1
    int index_in_block; // ποια εγγραφη του block ειμαστε
} HeapFileIterator;

#endif /* HP_FILE_STRUCTS_H */
