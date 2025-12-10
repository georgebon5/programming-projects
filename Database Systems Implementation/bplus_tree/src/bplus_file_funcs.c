#include "bplus_file_funcs.h"
#include "bplus_datanode.h"
#include "bf.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Macro για error handling - αν αποτύχει κάποια κλήση BF επιστρέφουμε -1
#define CALL_BF(call)         \
  {                           \
    BF_ErrorCode code = call; \
    if (code != BF_OK)        \
    {                         \
      BF_PrintError(code);    \
      return -1;              \
    }                         \
  }


int bplus_create_file(const TableSchema *schema, const char *fileName)
{
  // Δημιουργία νέου αρχείου
  CALL_BF(BF_CreateFile(fileName));
  
  // Άνοιγμα για να γράψουμε τα metadata
  int fd;
  CALL_BF(BF_OpenFile(fileName, &fd));
  
  // Δέσμευση πρώτου block για metadata
  BF_Block *meta_block;
  BF_Block_Init(&meta_block);
  CALL_BF(BF_AllocateBlock(fd, meta_block));
  
  // Αρχικοποίηση metadata structure
  BPlusMeta meta;
  meta.root_block_num = -1;  // αρχικά δεν έχουμε root
  meta.depth = 0;
  meta.data_block_count = 0;
  meta.index_block_count = 0;
  meta.table_schema = *schema;
  
  // Γράψιμο metadata στο block
  char *data = BF_Block_GetData(meta_block);
  memcpy(data, &meta, sizeof(BPlusMeta));
  
  BF_Block_SetDirty(meta_block);
  CALL_BF(BF_UnpinBlock(meta_block));
  BF_Block_Destroy(&meta_block);
  
  CALL_BF(BF_CloseFile(fd));
  
  return 0;
}


int bplus_open_file(const char *fileName, int *file_desc, BPlusMeta **metadata)
{
  // Άνοιγμα του αρχείου
  BF_ErrorCode code = BF_OpenFile(fileName, file_desc);
  
  if (code != BF_OK) {
    BF_PrintError(code);
    return -1;
  }
  
  // διάβασμα του πρώτου block που έχει τα metadata
  BF_Block *meta_block;
  BF_Block_Init(&meta_block);
  CALL_BF(BF_GetBlock(*file_desc, 0, meta_block));
  
  // δεσμευση μνημης για τα metadata
  *metadata = malloc(sizeof(BPlusMeta));
  if (*metadata == NULL) {
    BF_UnpinBlock(meta_block);
    BF_Block_Destroy(&meta_block);
    return -1;
  }
  
  // αντιγραφη των metadata απο το block
  char *data = BF_Block_GetData(meta_block);
  memcpy(*metadata, data, sizeof(BPlusMeta));
  
  CALL_BF(BF_UnpinBlock(meta_block));
  BF_Block_Destroy(&meta_block);
  
  return 0;
}

int bplus_close_file(const int file_desc, BPlusMeta* metadata)
{
  // πρεπει να σωσουμε τα metadata πισω στο αρχειο πριν κλεισουμε
  BF_Block *meta_block;
  BF_Block_Init(&meta_block);
  CALL_BF(BF_GetBlock(file_desc, 0, meta_block));
  
  // γραψιμο των updated metadata
  char *data = BF_Block_GetData(meta_block);
  memcpy(data, metadata, sizeof(BPlusMeta));
  
  BF_Block_SetDirty(meta_block);
  CALL_BF(BF_UnpinBlock(meta_block));
  BF_Block_Destroy(&meta_block);
  
  // κλεισιμο αρχειου
  CALL_BF(BF_CloseFile(file_desc));
  
  // ελευθερωση μνημης
  free(metadata);
  
  return 0;
}

int bplus_record_insert(const int file_desc, BPlusMeta *metadata, const Record *record)
{
  // βρισκουμε το key απο το record
  int key_idx = metadata->table_schema.key_index;
  int key = record->values[key_idx].int_value;
  
  
  BF_Block *block = NULL;
  BF_Block_Init(&block);
  
  
  // αν εχουμε αδειο δεντρο - φτιαχνουμε το πρωτο leaf
  if (metadata->root_block_num == -1) {
    
    BF_ErrorCode code = BF_AllocateBlock(file_desc, block);
    if (code != BF_OK) {
      BF_PrintError(code);
      BF_Block_Destroy(&block);
      return -1;
    }
    
    int block_count;
    code = BF_GetBlockCounter(file_desc, &block_count);
    if (code != BF_OK) {
      BF_PrintError(code);
      BF_UnpinBlock(block);
      BF_Block_Destroy(&block);
      return -1;
    }
    
    int new_block_id = block_count - 1;
    
    // αρχικοποιηση νεου data node
    BPlusDataNode node;
    node.is_leaf = 1;
    node.next_block = -1;
    node.key_count = 1;
    node.records[0] = *record;
    
    // γραψιμο στο block
    char *data = BF_Block_GetData(block);
    memcpy(data, &node, sizeof(BPlusDataNode));
    
    BF_Block_SetDirty(block);
    
    code = BF_UnpinBlock(block);
    if (code != BF_OK) {
      BF_PrintError(code);
    }
    
    BF_Block_Destroy(&block);
    
    // ενημερωση metadata
    metadata->root_block_num = new_block_id;
    metadata->data_block_count = 1;
    metadata->depth = 1;
    
    return new_block_id;
  }
  
  // αν υπαρχει ηδη δεντρο - ψαχνουμε το σωστο leaf
  int current_block_id = metadata->root_block_num;
  
  while (current_block_id != -1) {
    CALL_BF(BF_GetBlock(file_desc, current_block_id, block));
    
    char *data = BF_Block_GetData(block);
    BPlusDataNode node;
    memcpy(&node, data, sizeof(BPlusDataNode));
    
    // ελεγχος για duplicate key
    int i;
    for (i = 0; i < node.key_count; i++) {
      int existing_key = node.records[i].values[key_idx].int_value;
      if (existing_key == key) {
        // διπλοτυπο! δεν το επιτρεπουμε
        CALL_BF(BF_UnpinBlock(block));
        BF_Block_Destroy(&block);
        return -1;
      }
    }
    
    // αν ο κομβος εχει χωρο και το key ταιριαζει εδω
    if (node.key_count < 4) {
      int last_key = -1;
      if (node.key_count > 0) {
        last_key = node.records[node.key_count - 1].values[key_idx].int_value;
      }
      
      // αν το key πρεπει να μπει εδω (ειναι μεγαλυτερο απο το τελευταιο ή δεν υπαρχει επομενος)
      if (key > last_key || node.next_block == -1) {
        // βρισκουμε τη σωστη θεση (sorted insertion)
        int insert_pos = node.key_count;
        for (i = 0; i < node.key_count; i++) {
          int curr_key = node.records[i].values[key_idx].int_value;
          if (key < curr_key) {
            insert_pos = i;
            break;
          }
        }
        
        // μετακινηση records για να ανοιξουμε χωρο
        for (i = node.key_count; i > insert_pos; i--) {
          node.records[i] = node.records[i-1];
        }
        
        // εισαγωγη του νεου record
        node.records[insert_pos] = *record;
        node.key_count++;
        
        // αποθηκευση
        memcpy(data, &node, sizeof(BPlusDataNode));
        BF_Block_SetDirty(block);
        CALL_BF(BF_UnpinBlock(block));
        BF_Block_Destroy(&block);
        
        return current_block_id;
      }
    }
    
    // αν ο κομβος ειναι full και δεν υπαρχει επομενος, φτιαχνουμε νεο
    if (node.key_count >= 4 && node.next_block == -1) {
      int prev_block_id = current_block_id;
      
      // πρωτα κανουμε unpin τον τρεχοντα κομβο
      CALL_BF(BF_UnpinBlock(block));
      
      // δημιουργια νεου block για νεο leaf
      BF_Block *new_block;
      BF_Block_Init(&new_block);
      CALL_BF(BF_AllocateBlock(file_desc, new_block));
      int block_count;
      CALL_BF(BF_GetBlockCounter(file_desc, &block_count));
      int new_block_id = block_count - 1;
      
      // αρχικοποιηση νεου node
      BPlusDataNode new_node;
      new_node.is_leaf = 1;
      new_node.next_block = -1;
      new_node.key_count = 1;
      new_node.records[0] = *record;
      
      char *new_data = BF_Block_GetData(new_block);
      memcpy(new_data, &new_node, sizeof(BPlusDataNode));
      BF_Block_SetDirty(new_block);
      CALL_BF(BF_UnpinBlock(new_block));
      BF_Block_Destroy(&new_block);
      
      // τωρα ενημερωνουμε τον παλιο node να δειχνει στο νεο
      CALL_BF(BF_GetBlock(file_desc, prev_block_id, block));
      data = BF_Block_GetData(block);
      memcpy(&node, data, sizeof(BPlusDataNode));
      node.next_block = new_block_id;
      memcpy(data, &node, sizeof(BPlusDataNode));
      BF_Block_SetDirty(block);
      CALL_BF(BF_UnpinBlock(block));
      BF_Block_Destroy(&block);
      
      metadata->data_block_count++;
      
      return new_block_id;
    }
    
    // προχωραμε στον επομενο κομβο
    int next = node.next_block;
    CALL_BF(BF_UnpinBlock(block));
    current_block_id = next;
  }
  
  BF_Block_Destroy(&block);
  return -1;
}

int bplus_record_find(const int file_desc, const BPlusMeta *metadata, const int key, Record** out_record)
{  
  *out_record = NULL;
  
  // αν το δεντρο ειναι αδειο
  if (metadata->root_block_num == -1) {
    return -1;
  }
  
  BF_Block *block;
  BF_Block_Init(&block);
  
  int key_idx = metadata->table_schema.key_index;
  
  // διατρεχουμε τα leaf nodes μεσω του linked list
  int current_block_id = metadata->root_block_num;
  
  while (current_block_id != -1) {
    CALL_BF(BF_GetBlock(file_desc, current_block_id, block));
    
    char *data = BF_Block_GetData(block);
    BPlusDataNode node;
    memcpy(&node, data, sizeof(BPlusDataNode));
    
    // ψαχνουμε στα records του κομβου
    int i;
    for (i = 0; i < node.key_count; i++) {
      int curr_key = node.records[i].values[key_idx].int_value;
      
      if (curr_key == key) {
        *out_record = malloc(sizeof(Record));
        if (*out_record == NULL) {
          CALL_BF(BF_UnpinBlock(block));
          BF_Block_Destroy(&block);
          return -1;
        }
        
        memcpy(*out_record, &node.records[i], sizeof(Record));
        
        CALL_BF(BF_UnpinBlock(block));
        BF_Block_Destroy(&block);
        return 0;
      }
      
      //αν τα keys ειναι sorted και το curr_key > key, δεν χρειαζεται να συνεχισουμε
      if (curr_key > key) {
        break;
      }
    }
    
    // επομενος κομβος
    int next = node.next_block;
    CALL_BF(BF_UnpinBlock(block));
    current_block_id = next;
  }
  
  BF_Block_Destroy(&block);
  return -1; 
}

