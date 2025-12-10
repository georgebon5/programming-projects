#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "bf.h"
#include "hp_file_structs.h"
#include "record.h"

#define CALL_BF(call)         \
  {                           \
    BF_ErrorCode code = call; \
    if (code != BF_OK)        \
    {                         \
      BF_PrintError(code);    \
      return 0;        \
    }                         \
  }

int HeapFile_Create(const char* fileName)
{
  int fd;

  // φτιάξε και άνοιξε το αρχείο στο BF layer
  if (BF_CreateFile(fileName) != BF_OK) return 0;
  if (BF_OpenFile(fileName, &fd) != BF_OK) return 0;

  // δέσμευση του block 0 (header)
  BF_Block* b0 = NULL;
  BF_Block_Init(&b0);

  if (BF_AllocateBlock(fd, b0) != BF_OK) {
    BF_Block_Destroy(&b0);
    BF_CloseFile(fd);
    return 0;
  }

  void* base = BF_Block_GetData(b0);

  HeapFileHeader h;
  h.is_heap_file       = 1;
  h.last_data_block    = 0;
  h.total_records      = 0;
  h.records_per_block  = (BF_BLOCK_SIZE - (int)sizeof(int)) / (int)sizeof(Record);

  *(HeapFileHeader*)base = h;

  BF_Block_SetDirty(b0);
  BF_UnpinBlock(b0);
  BF_Block_Destroy(&b0);

  if (BF_CloseFile(fd) != BF_OK) return 0;
  return 1;
}


int HeapFile_Open(const char *fileName, int *file_handle, HeapFileHeader **header_info)
{
  // άνοιγμα του αρχείου από το επίπεδο BF
  if (BF_OpenFile(fileName, file_handle) != BF_OK) {
    BF_PrintError(BF_ERROR);
    return 0;
  }

  // παίρνουμε το πρώτο block (header)
  BF_Block *blk = NULL;
  BF_Block_Init(&blk);

  if (BF_GetBlock(*file_handle, 0, blk) != BF_OK) {
    BF_Block_Destroy(&blk);
    BF_CloseFile(*file_handle);
    return 0;
  }

  void *raw = BF_Block_GetData(blk);
  HeapFileHeader *temp = malloc(sizeof(HeapFileHeader));

  if (temp == NULL) {
    BF_UnpinBlock(blk);
    BF_Block_Destroy(&blk);
    BF_CloseFile(*file_handle);
    return 0;
  }

  memcpy(temp, raw, sizeof(HeapFileHeader));

  BF_UnpinBlock(blk);
  BF_Block_Destroy(&blk);

  // ένας μικρός έλεγχος εγκυρότητας, απλά για σιγουριά
  if (temp->is_heap_file != 1) {
    free(temp);
    BF_CloseFile(*file_handle);
    return 0;
  }

  *header_info = temp;
  return 1;
}


int HeapFile_Close(int file_handle, HeapFileHeader *hp_info)
{
  if (!hp_info) return 0;

  // γράψε πίσω τον header στο block 0 (αν το πάρουμε επιτυχώς)
  BF_Block *blk = NULL;
  BF_Block_Init(&blk);

  if (BF_GetBlock(file_handle, 0, blk) == BF_OK) {
    void *base = BF_Block_GetData(blk);
    // μονοκόμματη αντιγραφή struct (πιο “χειροποίητο” από memcpy)
    *(HeapFileHeader *)base = *hp_info;

    BF_Block_SetDirty(blk);
    BF_UnpinBlock(blk);
  }
  // ό,τι κι αν έγινε, καθάρισε τον πόρο του block
  BF_Block_Destroy(&blk);

  // ο header στη RAM δεν χρειάζεται άλλο
  free(hp_info);

  // τελικό κλείσιμο αρχείου
  if (BF_CloseFile(file_handle) != BF_OK) return 0;

  return 1;
}



int HeapFile_InsertRecord(int file_handle, HeapFileHeader *hp_info, const Record record)
{
  if (!hp_info || hp_info->records_per_block <= 0) return 0;

  BF_Block *blk = NULL;
  BF_Block_Init(&blk);

  int target = hp_info->last_data_block;

  // αν δεν υπάρχει κανένα data block, φτιάξε πρώτο
  if (target == 0) {
    if (BF_AllocateBlock(file_handle, blk) != BF_OK) {
      BF_Block_Destroy(&blk);
      return 0;
    }

    int total = 0;
    if (BF_GetBlockCounter(file_handle, &total) != BF_OK) {
      BF_UnpinBlock(blk);
      BF_Block_Destroy(&blk);
      return 0;
    }
    target = total - 1;

    char *raw0 = BF_Block_GetData(blk);
    *(int *)raw0 = 0;     // count = 0 στο νέο block
    BF_Block_SetDirty(blk);
    BF_UnpinBlock(blk);

    hp_info->last_data_block = target;
  }

  // δούλεψε στο "τελευταίο" block
  if (BF_GetBlock(file_handle, target, blk) != BF_OK) {
    BF_Block_Destroy(&blk);
    return 0;
  }

  char *base = BF_Block_GetData(blk);
  int  *cnt  = (int *)base;
  int   cap  = hp_info->records_per_block;
  Record *arr = (Record *)(base + (int)sizeof(int));

  if (*cnt < cap) {
    arr[*cnt] = record;   // γράψε & αύξησε
    (*cnt)++;
    BF_Block_SetDirty(blk);
    BF_UnpinBlock(blk);
  } else {
    // γέμισε → νέο block
    BF_UnpinBlock(blk);

    if (BF_AllocateBlock(file_handle, blk) != BF_OK) {
      BF_Block_Destroy(&blk);
      return 0;
    }

    int total = 0;
    if (BF_GetBlockCounter(file_handle, &total) != BF_OK) {
      BF_UnpinBlock(blk);
      BF_Block_Destroy(&blk);
      return 0;
    }
    int fresh = total - 1;

    char *base2 = BF_Block_GetData(blk);
    int  *cnt2  = (int *)base2;
    Record *arr2 = (Record *)(base2 + (int)sizeof(int));

    *cnt2 = 1;
    arr2[0] = record;

    BF_Block_SetDirty(blk);
    BF_UnpinBlock(blk);

    hp_info->last_data_block = fresh;
  }

  BF_Block_Destroy(&blk);
  hp_info->total_records += 1;   // θα γραφτεί μόνιμα στο Close
  return 1;
}




HeapFileIterator HeapFile_CreateIterator(int file_handle, HeapFileHeader* header_info, int id)
{
  HeapFileIterator out;
  out.file_handle = file_handle;
  out.header = header_info;
  out.search_id = id;
  out.current_block = 0;
  out.index_in_block = 0;

  //αν το αρχειο δεν εχει δεδομενα ή δεν ανοιγει
  if(header_info == NULL || header_info->total_records <= 0){
    return out;
  }
  
  // το προτο μπλοκ που περειχει εγγραφες ειναι παντα το 1 
  out.current_block = 1;
  out.index_in_block = 0;

  return out;
}


int HeapFile_GetNextRecord(HeapFileIterator* heap_iterator, Record** record)
{
    *record = NULL;

    if (!heap_iterator || !record || !heap_iterator->header)
        return 0;

    // άδειος ή τελειωμένος iterator
    if (heap_iterator->current_block == 0)
        return 0;

    BF_Block* blk = NULL;
    BF_Block_Init(&blk);

    while (heap_iterator->current_block <= heap_iterator->header->last_data_block) {
        if (BF_GetBlock(heap_iterator->file_handle, heap_iterator->current_block, blk) != BF_OK) {
            BF_Block_Destroy(&blk);
            return 0;
        }

        char* base = BF_Block_GetData(blk);
        int count = *(int*)base;
        Record* slots = (Record*)(base + sizeof(int));

        // ψάξε μέσα στο block
        while (heap_iterator->index_in_block < count) {
            Record* cur = &slots[heap_iterator->index_in_block++];

            // -1 σημαίνει "φέρε τα όλα"
            if (heap_iterator->search_id == -1 || cur->id == heap_iterator->search_id) {
                Record* copy = malloc(sizeof(Record));
                if (!copy) { BF_UnpinBlock(blk); BF_Block_Destroy(&blk); return 0; }

                *copy = *cur;
                *record = copy;  // εδώ επιστρέφουμε τη νέα εγγραφή

                BF_UnpinBlock(blk);
                BF_Block_Destroy(&blk);
                return 1;
            }
        }

        // αν τελείωσε το block, πάμε στο επόμενο
        heap_iterator->current_block++;
        heap_iterator->index_in_block = 0;
        BF_UnpinBlock(blk);
    }

    BF_Block_Destroy(&blk);
    return 0; 
}

