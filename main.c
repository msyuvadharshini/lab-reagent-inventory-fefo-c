/* Lab Reagent Inventory and FEFO Allocation -- educational C11 prototype.
 * Whole packs/bottles/kits only; never use this to make clinical decisions.
 * FEFO = First Expiry, First Out. Fixed arrays; no extra C libraries.
 */
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define READ_END (-1)
#define READ_BAD 0
#define READ_OK 1
#define DATE_LEN 11
#define LINE_LEN 256
#define MAX_BATCHES 300
#define ID_LEN 24
#define CODE_LEN 24
#define NAME_LEN 60
#define UNIT_LEN 12
#define MAX_QUANTITY 1000000L
#define DATA_FILE "reagent_batches.txt"
#define TEMP_FILE "reagent_batches.txt.tmp"
#define BACKUP_FILE "reagent_batches.txt.bak"

/* Even at full capacity, summing all valid quantities cannot overflow long. */
_Static_assert(MAX_BATCHES <= LONG_MAX / MAX_QUANTITY,
               "Inventory totals must fit in long.");

typedef struct {
    char id[ID_LEN];
    char reagentCode[CODE_LEN];
    char name[NAME_LEN];
    char unit[UNIT_LEN];
    char expiryDate[DATE_LEN];
    long quantity;
} Batch;

/* Read and consume a WHOLE line, even if it is too long for the buffer.
 * Return 1 for a line, 0 for end-of-file, -1 for an invalid line/read error.
 * CRLF and a final line without a newline are supported. */
static int readRawLine(FILE *stream, char *out, size_t capacity) {
    size_t used = 0;
    int ch, bad = 0;
    while ((ch = fgetc(stream)) != '\n' && ch != EOF) {
        if (ch == '\0') bad = 1;
        if (used + 1 < capacity) out[used++] = (char)ch;
        else bad = 1;
    }
    out[used] = '\0';
    if (ferror(stream)) return -1;
    if (ch == EOF && used == 0 && !bad) return 0;
    if (used > 0 && out[used - 1] == '\r') out[--used] = '\0';
    return bad ? -1 : 1;
}

/* Spaces inside names are allowed; empty fields, control characters,
 * leading/trailing whitespace, and the file separator '|' are not. */
static int validText(const char *text, size_t capacity) {
    size_t length = strlen(text);
    if (length == 0 || length >= capacity) return 0;
    if (isspace((unsigned char)text[0]) ||
        isspace((unsigned char)text[length - 1])) return 0;
    for (size_t i = 0; i < length; i++)
        if (!isprint((unsigned char)text[i]) || text[i] == '|') return 0;
    return 1;
}

static int readText(const char *prompt, char *out, size_t capacity) {
    char line[LINE_LEN];
    size_t start = 0, length;
    int result;
    fputs(prompt, stdout);
    fflush(stdout);
    result = readRawLine(stdin, line, sizeof line);
    if (result == 0 || ferror(stdin)) return READ_END;
    if (result < 0) {
        puts("Invalid input: line too long or contains a null character.");
        return READ_BAD;
    }
    length = strlen(line);
    while (length > 0 && isspace((unsigned char)line[length - 1]))
        line[--length] = '\0';
    while (isspace((unsigned char)line[start])) start++;
    if (start > 0) memmove(line, line + start, length - start + 1);
    if (!validText(line, capacity)) {
        printf("Invalid input: use 1 to %zu printable characters; no '|'.\n",
               capacity - 1);
        return READ_BAD;
    }
    strcpy(out, line); /* Length was checked before copying. */
    return READ_OK;
}

static int validId(const char *id) {
    if (id[0] == '\0') return 0;
    for (size_t i = 0; id[i] != '\0'; i++)
        if (!isalnum((unsigned char)id[i]) && id[i] != '-' && id[i] != '_')
            return 0;
    return 1;
}

static int readId(const char *prompt, char *out, size_t capacity) {
    int result = readText(prompt, out, capacity);
    if (result != READ_OK) return result;
    if (!validId(out)) {
        puts("Invalid ID: use letters, digits, '-' or '_' only.");
        return READ_BAD;
    }
    return READ_OK;
}

/* Check EXACTLY YYYY-MM-DD, including leap years. No sscanf signs or
 * shortened month/day fields are accepted. Supported years: 2000-9999. */
static int validDate(const char *date) {
    int year, month, day;
    int days[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (strlen(date) != 10 || date[4] != '-' || date[7] != '-') return 0;
    for (int i = 0; i < 10; i++)
        if (i != 4 && i != 7 && !isdigit((unsigned char)date[i])) return 0;
    year = (date[0] - '0') * 1000 + (date[1] - '0') * 100 +
           (date[2] - '0') * 10 + date[3] - '0';
    month = (date[5] - '0') * 10 + date[6] - '0';
    day = (date[8] - '0') * 10 + date[9] - '0';
    if (year < 2000 || month < 1 || month > 12) return 0;
    if (year % 400 == 0 || (year % 4 == 0 && year % 100 != 0)) days[1] = 29;
    return day >= 1 && day <= days[month - 1];
}

static int readDate(const char *prompt, char *out) {
    int result = readText(prompt, out, DATE_LEN);
    if (result != READ_OK) return result;
    if (!validDate(out)) {
        puts("Invalid date: use a real YYYY-MM-DD date (years 2000-9999).");
        return READ_BAD;
    }
    return READ_OK;
}

/* Missing data means a fresh project, NOT an unreadable data file.
 * A backup without a main file is treated as a recovery situation. */
static FILE *openDataFile(int *ok) {
    FILE *fp = fopen(DATA_FILE, "r");
    *ok = 1;
    if (fp != NULL) return fp;
    if (errno != ENOENT) {
        fprintf(stderr, "Cannot read %s. No changes made.\n", DATA_FILE);
        *ok = 0;
        return NULL;
    }
    fp = fopen(BACKUP_FILE, "r");
    if (fp != NULL) {
        fclose(fp);
        fprintf(stderr, "Main data file missing, but %s exists.\n"
                "Restore the backup as %s before running again.\n",
                BACKUP_FILE, DATA_FILE);
        *ok = 0;
    } else if (errno != ENOENT) {
        fprintf(stderr, "Cannot check backup file. No changes made.\n");
        *ok = 0;
    }
    return NULL;
}

/* Called ONLY after every record was written and the temporary file
 * closed successfully. Keep the previous main file as a .bak file.
 * Standard C rename steps are used, so this also works with Windows GCC.
 * This is not a power-failure-safe database transaction. */
static int commitFile(void) {
    int hadOldFile;
    if (remove(BACKUP_FILE) != 0 && errno != ENOENT) {
        puts("Save failed: cannot replace the backup. No changes saved.");
        remove(TEMP_FILE);
        return 0;
    }
    hadOldFile = rename(DATA_FILE, BACKUP_FILE) == 0;
    if (!hadOldFile && errno != ENOENT) {
        puts("Save failed: cannot back up the data file. No changes saved.");
        remove(TEMP_FILE);
        return 0;
    }
    if (rename(TEMP_FILE, DATA_FILE) != 0) {
        puts("Save failed: cannot install the new data file.");
        if (hadOldFile && rename(BACKUP_FILE, DATA_FILE) != 0)
            printf("Restore %s as %s before running again.\n",
                   BACKUP_FILE, DATA_FILE);
        remove(TEMP_FILE);
        return 0;
    }
    return 1;
}


/* Only decimal digits are accepted: no sign, fraction, exponent or suffix.
 * Zero is allowed for saved/used-up lots and report thresholds, not receipts
 * or issue requests. strtol + ERANGE also rejects enormous pasted numbers. */
static int parseQuantity(const char *text, long minimum, long *value) {
    char *end;
    long number;
    if (text[0] == '\0') return 0;
    for (size_t i = 0; text[i] != '\0'; i++)
        if (!isdigit((unsigned char)text[i])) return 0;
    errno = 0;
    number = strtol(text, &end, 10);
    if (errno == ERANGE || *end != '\0' ||
        number < minimum || number > MAX_QUANTITY) return 0;
    *value = number;
    return 1;
}

static int readQuantity(const char *prompt, long minimum, long *value) {
    char text[32];
    int result = readText(prompt, text, sizeof text);
    if (result != READ_OK) return result;
    if (!parseQuantity(text, minimum, value)) {
        printf("Invalid quantity: enter digits only, from %ld to %ld.\n",
               minimum, MAX_QUANTITY);
        return READ_BAD;
    }
    return READ_OK;
}

static int findBatch(const Batch batches[], int count, const char *id) {
    for (int i = 0; i < count; i++)
        if (strcmp(batches[i].id, id) == 0) return i;
    return -1;
}

static int findProduct(const Batch batches[], int count, const char *code) {
    for (int i = 0; i < count; i++)
        if (strcmp(batches[i].reagentCode, code) == 0) return i;
    return -1;
}

static int loadBatches(Batch batches[]) {
    int ok, count = 0, lineNumber = 0, result;
    FILE *fp = openDataFile(&ok);
    char line[LINE_LEN], quantityText[32], extra;
    Batch item;
    if (fp == NULL) return ok ? 0 : -1;
    while ((result = readRawLine(fp, line, sizeof line)) != 0) {
        int existing;
        lineNumber++;
        /* Widths leave room for '\0'; %c detects unwanted extra text. */
        if (result < 0 || count >= MAX_BATCHES ||
            sscanf(line, "%23[^|]|%23[^|]|%59[^|]|%11[^|]|%10[^|]|%31[^|]%c",
                   item.id, item.reagentCode, item.name, item.unit,
                   item.expiryDate, quantityText, &extra) != 6 ||
            !validText(item.id, sizeof item.id) || !validId(item.id) ||
            !validText(item.reagentCode, sizeof item.reagentCode) ||
            !validId(item.reagentCode) || !validText(item.name, sizeof item.name) ||
            !validText(item.unit, sizeof item.unit) || !validDate(item.expiryDate) ||
            !parseQuantity(quantityText, 0, &item.quantity) ||
            findBatch(batches, count, item.id) >= 0) {
            fprintf(stderr, "Cannot load %s at line %d: invalid, duplicate, "
                    "or excess batch. No changes made.\n", DATA_FILE, lineNumber);
            fclose(fp);
            return -1;
        }
        existing = findProduct(batches, count, item.reagentCode);
        if (existing >= 0 && (strcmp(item.name, batches[existing].name) != 0 ||
                             strcmp(item.unit, batches[existing].unit) != 0)) {
            fprintf(stderr, "Cannot load line %d: inconsistent product name/unit "
                    "for reagent code. No changes made.\n", lineNumber);
            fclose(fp);
            return -1;
        }
        batches[count++] = item;
    }
    if (fclose(fp) != 0) {
        fprintf(stderr, "Cannot finish reading %s. No changes made.\n", DATA_FILE);
        return -1;
    }
    return count;
}

static int saveBatches(const Batch batches[], int count) {
    FILE *fp = fopen(TEMP_FILE, "w");
    int ok = 1;
    if (fp == NULL) {
        puts("Save failed: cannot create temporary file. No changes saved.");
        return 0;
    }
    for (int i = 0; i < count; i++) {
        if (fprintf(fp, "%s|%s|%s|%s|%s|%ld\n", batches[i].id,
                    batches[i].reagentCode, batches[i].name, batches[i].unit,
                    batches[i].expiryDate, batches[i].quantity) < 0) {
            ok = 0;
            break;
        }
    }
    if (fclose(fp) != 0) ok = 0;
    if (!ok) {
        puts("Save failed while writing. No changes saved.");
        remove(TEMP_FILE);
        return 0;
    }
    return commitFile();
}

static int addBatch(Batch batches[], int *count) {
    Batch item;
    int existing, result;
    if (*count >= MAX_BATCHES) {
        puts("Batch limit reached (300). No changes made.");
        return READ_OK;
    }
    result = readId("Unique batch record ID: ", item.id, sizeof item.id);
    if (result != READ_OK) return result;
    if (findBatch(batches, *count, item.id) >= 0) {
        puts("Duplicate batch ID. No changes made.");
        return READ_OK;
    }
    result = readId("Reagent code: ", item.reagentCode, sizeof item.reagentCode);
    if (result != READ_OK) return result;
    existing = findProduct(batches, *count, item.reagentCode);
    if (existing >= 0) {
        strcpy(item.name, batches[existing].name);
        strcpy(item.unit, batches[existing].unit);
        printf("Using saved product: %s [%s].\n", item.name, item.unit);
    } else {
        result = readText("Reagent name: ", item.name, sizeof item.name);
        if (result != READ_OK) return result;
        result = readText("Stock unit (e.g. packs): ", item.unit, sizeof item.unit);
        if (result != READ_OK) return result;
    }
    result = readDate("Expiry date (YYYY-MM-DD): ", item.expiryDate);
    if (result != READ_OK) return result;
    result = readQuantity("Quantity received: ", 1, &item.quantity);
    if (result != READ_OK) return result;
    batches[*count] = item;
    if (saveBatches(batches, *count + 1)) {
        (*count)++;
        puts("Batch saved successfully.");
    }
    return READ_OK;
}

static void listBatches(const Batch batches[], int count) {
    if (count == 0) {
        puts("No reagent batches found.");
        return;
    }
    puts("\nNames are shortened here; Search displays full details.");
    printf("%-23s %-23s %-25s %-11s %-10s %8s\n",
           "Batch ID", "Reagent code", "Name", "Unit", "Expiry", "Quantity");
    for (int i = 0; i < count; i++)
        printf("%-23s %-23s %-25.25s %-11s %-10s %8ld\n", batches[i].id,
               batches[i].reagentCode, batches[i].name, batches[i].unit,
               batches[i].expiryDate, batches[i].quantity);
}

static int searchBatch(const Batch batches[], int count) {
    char id[ID_LEN];
    int index, result = readId("Batch ID to search: ", id, sizeof id);
    if (result != READ_OK) return result;
    index = findBatch(batches, count, id);
    if (index < 0) puts("Batch ID not found.");
    else printf("\nBatch ID: %s\nReagent code: %s\nName: %s\nUnit: %s\n"
                "Expiry date: %s\nQuantity: %ld\n", batches[index].id,
                batches[index].reagentCode, batches[index].name,
                batches[index].unit, batches[index].expiryDate, batches[index].quantity);
    return READ_OK;
}

/* Strict order: earliest expiry first; equal dates use lexicographic batch ID.
 * Sort INDICES, not the saved records, so file order is not changed. */
static int earlier(const Batch *a, const Batch *b) {
    int comparison = strcmp(a->expiryDate, b->expiryDate);
    return comparison < 0 || (comparison == 0 && strcmp(a->id, b->id) < 0);
}

static int planIssue(const Batch batches[], int count, const char *code,
                     const char *asOf, long requested, long take[],
                     int order[], long *available) {
    int eligible = 0;
    long remaining = requested;
    *available = 0;
    for (int i = 0; i < count; i++) {
        take[i] = 0;
        /* Classroom rule: a batch is valid through its recorded expiry date. */
        if (strcmp(batches[i].reagentCode, code) == 0 && batches[i].quantity > 0 &&
            strcmp(batches[i].expiryDate, asOf) >= 0) {
            order[eligible++] = i;
            *available += batches[i].quantity;
        }
    }
    /* Insertion sort is small, deterministic and easy to explain: O(k^2). */
    for (int i = 1; i < eligible; i++) {
        int key = order[i], j = i;
        while (j > 0 && earlier(&batches[key], &batches[order[j - 1]])) {
            order[j] = order[j - 1];
            j--;
        }
        order[j] = key;
    }
    if (*available < requested) return eligible; /* No partial plan accepted. */
    for (int i = 0; i < eligible && remaining > 0; i++) {
        int index = order[i];
        take[index] = batches[index].quantity < remaining ? batches[index].quantity : remaining;
        remaining -= take[index];
    }
    return eligible;
}

static int issueStock(Batch batches[], int count) {
    char code[CODE_LEN], asOf[DATE_LEN], answer[8];
    long requested, available, take[MAX_BATCHES];
    int order[MAX_BATCHES], eligible, product, result;
    result = readId("Reagent code to issue: ", code, sizeof code);
    if (result != READ_OK) return result;
    product = findProduct(batches, count, code);
    if (product < 0) {
        puts("Reagent code not found.");
        return READ_OK;
    }
    result = readDate("Issue date (YYYY-MM-DD): ", asOf);
    if (result != READ_OK) return result;
    result = readQuantity("Quantity requested: ", 1, &requested);
    if (result != READ_OK) return result;
    eligible = planIssue(batches, count, code, asOf, requested, take, order, &available);
    if (available < requested) {
        printf("Insufficient valid stock: available=%ld, requested=%ld [%s]. "
               "No stock changed.\n", available, requested, batches[product].unit);
        return READ_OK;
    }
    printf("\nFEFO PLAN: %s | %s | as of %s\n", code, batches[product].name, asOf);
    for (int i = 0; i < eligible; i++) {
        int index = order[i];
        if (take[index] > 0)
            printf("%s | expires %s | issue %ld %s\n", batches[index].id,
                   batches[index].expiryDate, take[index], batches[index].unit);
    }
    printf("Requested=%ld, Available=%ld [%s]. Expired/empty batches excluded.\n",
           requested, available, batches[product].unit);
    result = readText("Confirm issue? (y/n): ", answer, sizeof answer);
    if (result != READ_OK) return result;
    if (strcmp(answer, "n") == 0 || strcmp(answer, "N") == 0) {
        puts("Issue cancelled. No stock changed.");
        return READ_OK;
    }
    if (strcmp(answer, "y") != 0 && strcmp(answer, "Y") != 0) {
        puts("Issue cancelled: enter y or n. No stock changed.");
        return READ_OK;
    }
    for (int i = 0; i < count; i++) batches[i].quantity -= take[i];
    if (saveBatches(batches, count))
        printf("Issue saved successfully. Quantity issued: %ld %s.\n",
               requested, batches[product].unit);
    else {
        for (int i = 0; i < count; i++) batches[i].quantity += take[i];
        puts("Quantities restored in memory; issue was not saved.");
    }
    return READ_OK;
}

static int stockReport(const Batch batches[], int count) {
    char asOf[DATE_LEN];
    long threshold;
    int valid = 0, expired = 0, empty = 0, low = 0, result;
    if (count == 0) {
        puts("No reagent batches found.");
        return READ_OK;
    }
    result = readDate("Report date (YYYY-MM-DD): ", asOf);
    if (result != READ_OK) return result;
    result = readQuantity("Low-stock threshold (each product's own unit): ", 0, &threshold);
    if (result != READ_OK) return result;
    printf("\nBATCH STATUS AS OF %s\n", asOf);
    for (int i = 0; i < count; i++) {
        const char *status;
        if (batches[i].quantity == 0) { status = "EMPTY"; empty++; }
        else if (strcmp(batches[i].expiryDate, asOf) < 0) { status = "EXPIRED"; expired++; }
        else { status = "ELIGIBLE"; valid++; }
        printf("%s | %s | %s | quantity=%ld %s | expiry=%s\n", batches[i].id,
               batches[i].reagentCode, status, batches[i].quantity,
               batches[i].unit, batches[i].expiryDate);
    }
    puts("\nAVAILABLE STOCK BY REAGENT (expired stock excluded)");
    for (int i = 0; i < count; i++) {
        long total = 0;
        if (findProduct(batches, i, batches[i].reagentCode) >= 0) continue;
        for (int j = 0; j < count; j++)
            if (strcmp(batches[j].reagentCode, batches[i].reagentCode) == 0 &&
                strcmp(batches[j].expiryDate, asOf) >= 0)
                total += batches[j].quantity;
        if (total <= threshold) low++;
        printf("%s | %s | available=%ld %s | %s (threshold=%ld)\n",
               batches[i].reagentCode, batches[i].name, total, batches[i].unit,
               total <= threshold ? "LOW" : "OK", threshold);
    }
    printf("Batch summary: Eligible=%d, Expired=%d, Empty=%d, Total=%d\n",
           valid, expired, empty, count);
    printf("Low-stock reagent codes: %d\n", low);
    return READ_OK;
}

int main(void) {
    Batch batches[MAX_BATCHES];
    char choice[8];
    int count = loadBatches(batches), result = READ_OK;
    if (count < 0) return 1;
    puts("Educational inventory simulation. Use fictitious records only.");
    while (result != READ_END) {
        puts("\nLAB REAGENT INVENTORY AND FEFO ALLOCATION\n"
             "1. Receive a batch\n2. List batches\n3. Search batch ID\n"
             "4. Plan and confirm FEFO issue\n5. Stock and expiry report\n6. Exit");
        result = readText("Choose an option: ", choice, sizeof choice);
        if (result != READ_OK) continue;
        switch (strlen(choice) == 1 ? choice[0] : '?') {
            case '1': result = addBatch(batches, &count); break;
            case '2': listBatches(batches, count); break;
            case '3': result = searchBatch(batches, count); break;
            case '4': result = issueStock(batches, count); break;
            case '5': result = stockReport(batches, count); break;
            case '6': puts("Exiting inventory. Thank you."); return 0;
            default: puts("Invalid option. Choose 1 to 6."); break;
        }
    }
    puts("\nInput ended. Any incomplete operation was cancelled.");
    return ferror(stdin) ? 1 : 0;
}
