#include <iostream>     // για χρηση input και output
#include <vector>       // για χρηση δυναμικων αποθηκευσεων δεδομενων
#include <string>       // για χρηση συμβολοσειρων 
#include <fstream>      // για εγγραφη και διαβασμα αρχειων
#include <sstream>      // για χρηση της κλασης stringstream
#include <algorithm>    // για χρηση ταξινομησης δεδομενων  
#include <locale>


using namespace std;
//αυτη η συναρτηση χρησιμοποιειται στην κλασση του Προιοντος και οριζεται αργοτερα

// διαγραφη των κενων χαρακτηρων απο την αρχη της συμβολοσειρας
static inline void ltrim(std::string &s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](unsigned char ch) {
        return !std::isspace(ch);
    }));
}

// διαγραφη των κενων χαρακτηρων απο το τελος της συμβολοσειρας
static inline void rtrim(std::string &s) {
    s.erase(std::find_if(s.rbegin(), s.rend(), [](unsigned char ch) {
        return !std::isspace(ch);
    }).base(), s.end());
}

// αφαιρει τους κενους χαρακτηρες και απο τις δυο πλευρες
static inline void trim(std::string &s) {
    ltrim(s);
    rtrim(s);
}

class Product{      // κλαση προιον
protected:          // προστατευομενα μελοι
    string title;   
    string description;
    string category;
    string subcategory;
    float price;
    string UnitType;
    float quantity;
    int Sold=0;
public:
    // constructor με initializer list ωστε καθε φορα που δημιουργειται αντικειμενο της κλασης να αρχικοποιουνται τα μελοι του 
    Product (string t, string d, string c, string sc, float p, string ut, float q):title(t), description(d), category(c), subcategory(sc), price(p), UnitType(ut), quantity(q){
        cout << "Product created.\n";
    }

    void DisplayProductInfo(){      // συναρτηση για εκτυπωση των στοιχειων ενος προιοντος 
        cout << "Title: " << title << endl;
        cout << ", Description: " << description << endl;
        cout << ", Category: " << category << endl;
        cout << ", Subcategory: " << subcategory << endl;
        cout << ", Price: " << price << " / " << UnitType << endl;
        cout << ", Quantity: " << quantity << " " << UnitType << " left." << endl;
    }

    void setDescription(string newDescription){    // αν θελω να αλλαξω την  περιγραφη ενος προιοντος 
        description = newDescription;
    }


    string getDescription() {   // επιστροφη της περιγραφης ενος προιοντος 
        return description;
    }

    void setPrice(float newPrice){  // αλλαγη της τιμης ενος προιοντος 
        price = newPrice;
    }
    float getPrice() const {    // συναρτηση επιστροφης της τιμης ενος προιοντος 
        return price; 
    }
    
    void setQuantity(float newQuantity){    // αλλαγη της ποσοτητας ενος προιοντος 
        if(newQuantity < 0){    // αν η ποσοτητα ειναι αρνητικη τοτε να μηδενιζει
            quantity = 0;
        }else{
            quantity = newQuantity;
        }
    }
    float getQuantity() const {     // συναρτηση επιστροφης της ποσοτητας
        return quantity; 
    }

    string getTitle() const {   // συναρτηση για επιστροφη του τιτλου 
        return title; 
    }
    string getCategory() const {    // επιστροφη κατηγοριας προιοντος 
        return category; 
    }
    string getSubcategory() const {     // επιστροφη υποκατηγοριας προιοντος 
        return subcategory; 
    }
    int getSold() const {   // συναρτηση επιστροφηςγια τις συνολικες πωλησεις ενος προιοντος απο ολους τους χρηστες
        return Sold;
    }

    void setSold(int amount) {  // αλλαγη της τιμης για τις συνολικες πωλησεις ενος προιοντος
        Sold += amount;
    }
    
    string toString() const {  // βοηθιτικη συναρτηση για να λειτουγισει η saveProductsToFile που ΞΑΝΑ γραφει τα καινουρια στοιχεια του προιοντος στο αρχειο
        stringstream ss;
        ss << title << " @ " << description << " @ " << category << " @ " << subcategory << " @ " << price << " @ " << UnitType << " @ " << quantity;
        return ss.str();
    }
};
// το παρακατω struct περιεχει εναν operator για να κανει ταξινομηση των προιοντων με βαση της συνολικες πωλησεις τους ωστε να βρεθουν τα best seller προιοντα 
struct CompareBySold {
    bool operator()(const Product& a, const Product& b) const {
        return a.getSold() > b.getSold();  // Descending order
    }
};
//συναρτηση για να περναει στα αρχεία ις αλλαγες
void saveProductsToFile(const string& filename, const vector<Product>& products) {// συναρτηση για αποθήκευση αλλαγων στο αρχειο των προϊόντων
    ofstream file(filename);
    if (!file.is_open()) {
        cout << "Failed to open file: " << filename << endl;
        return;
    }

    for (const Product& p : products) {
        file << p.toString() << endl;
    }

    file.close();
}

class Cart {    // κλαση καλαθι
protected:    // το struct αυτο περιεχει ενα αντικειμενο τυπου Product που μπιανει στο καλαθι, την ποοοτητα του προιντος που μπαινει στο καλαθι και τον κατασκευαστη του Item
    struct Item {
        Product product;
        int quantity;
        Item(Product* product, int quantity) : product(*product), quantity(quantity) {}
    };
    vector<Item> items;    // στο vector αυτο μπαινουν τα προιαντα με τα χαρακτηριστικα τους που βρισκονται στο καλαθι
    float totalCost;    // συνολικο κοστος
    string cartOwner;    // το ονομα του ιδιοκτητη του καλαθου
public:

    static int cart_number;    // πληθος καλαθιων
    Cart(){    // defult constructor της κλασης Cart
        cartOwner = "Test";
    }
    Cart(const string& owner) : cartOwner(owner), totalCost(0) {}    // constructor της κλασης Item

    void setCartOwner(const string& owner) {    // αλλαγη του cartowner 
        cartOwner = owner;
    }
    string getCartOwner() const {    // επιστροφη του cartowner
        return cartOwner;
    }

    void setTotalCost(float totalCost_) {    // αλλαγη του συνολικου κοστους του καλαθιου
        totalCost = totalCost_;
    }

    float getTotalCost() const {    // επιστροφη του συνολικου κοστους του καλαθιου
        return totalCost;
    }

    float CgetQuantity(Item& product) {    // επιστροφη της ποσοτητα του προιοντος που βρισκεται στο καλαθι 
        return product.quantity;
    }

    void addItem(Product& product, int quantity) {    // προσθηκη προιοντος στο καλαθι μαζι με την αντιστοιχη ποσοτητα 
        if (quantity > product.getQuantity()) {    // αν η ποσοτητα του προιοντος που επελεξε ο πελατης ειναι μεγαλυτερη απο αυτη που διατιθεται τοτε εκτυπωνει καταλληλο μηνυμα και τερματιζει η συναρτηση
            cout << "There is not enough " << product.getTitle() << " available." << endl;
            return;
        }

        for (vector<Item>::iterator it = items.begin(); it != items.end(); ++it) {
            // Αν το προιον βρισκεται ειδη μεσα στο καλαθι
            if (it->product.getTitle() == product.getTitle()) {
                if (it->quantity + quantity > product.getQuantity()) {    // σε περιπτωση που δεν ειναι αρκετη η διαθεσιμη ποσοτητα
                    cout << "There is not enough " << product.getTitle() << " available." << endl;
                    return;
                }
                // προσθεση της ποσοτητας
                it->quantity += quantity;
                // υπολογισμος τρεχουμενου συνολικου κοστους 
                totalCost += quantity * product.getPrice();
                cout << "Product added successfully." << endl;
                return;
            }
        }
        // προσθηκη νεου προιοντος στο vector και υπολογισμος του συνολικου κοστους 
        items.emplace_back(&product, quantity);
        totalCost += quantity * product.getPrice();
        product.setSold(product.getSold() + quantity);
        cout << "Total cost: " << totalCost << endl;
    }

    // συναρτηση για αφαιρεση προιοντος απο το καλαθι
    void removeItem(Product& product, int quantity) {
        for (vector<Item>::iterator it = items.begin(); it != items.end(); ++it) {
            // Αν το προιον βρεθει εντος του καλαθιου
            if (it->product.getTitle() == product.getTitle()) {
                // σε περιπτωση που η ζητουμενη ποσοτητα ειναι μεγαλυτερη απο την προσφερομενη τερματιζει
                if (it->quantity < quantity) {
                    cout << "There's only " << product.getTitle() << " available in the cart." << endl;
                    return;
                // κανει κανονικα αφαιρεση του προιοντος αφου το προιον και η ποσοτητα υπαρχουν και η ζητουμενη ποσοτητα ειναι ιση με την προσφερομενη
                } else if (it->quantity == quantity) {
                    //
                    items.erase(it); // αφαιρει το προιον που δειχνει ο δεικτης απο το vector 
                    totalCost -= quantity * product.getPrice(); // μειωση του συνολικου κοστους
                    product.setSold(product.getSold() - quantity); // αφαιρεση και της συνολικης ποσοτητας ολων των χρηστων
                    cout << "Product removed from the cart successfully." << endl;
                    return;
                }

                // σε περιπτωση που η ζητουμενη ποσοτητα ειναι μικροτερη απο την προσφερομενη 
                it->quantity -= quantity;   // μειωση της ποσοτητας 
                totalCost -= quantity * product.getPrice(); // μειωση του συνολικου κοστους 
                cout << "Product's quantity updated successfully." << endl;
                cout << "Total cost: " << totalCost << endl;
                return;
            }
        }
        // Αν δεν βρεθει το προιον 
        cout << "Product not found in the cart." << endl;
    }

    // συναρτηση για εμφανιση του καλαθιου 
    void printCart() {
        cout << endl << "---CART START---" << endl;
        for (vector<Item>::const_iterator it = items.begin(); it != items.end(); ++it) {
            cout << it->quantity << " " << it->product.getTitle() << endl;  // εκτυπωση ποστοτητας και τιτλου του προιοντος 
        }
        cout << "---CART END---" << endl;
        cout << "Total cost: " << totalCost << endl;    // εκτυπωση συνολικου κοστους
    }

    // συναρτηση για την πληρωμη της παραγγελιας
    void checkout() {
        printCart();    // εμφανιση του καλαθιου
        cout << "ORDER COMPLETED" << endl;
        save_order_history();   // ιστορικο παραγγελιωμ
        items.clear();  // καθαρισμος καλαθιου 
    }

    // συναρτηση για το ιστορικο παραγγελιων
    void save_order_history() {
        // ακολουθει το filepath
        string folder = "files/order_history/";
        string filename = folder + cartOwner + "_history.txt";  // το filepath περιεχει το ονομα του πελατη

        // Έλεγχος για το αν υπάρχει ο φάκελος (χρησιμοποιώντας εντολή συστήματος)
        if (system(("mkdir -p " + folder).c_str()) != 0) {
            cout << "Error: Cannot create directory " << folder << endl;
            return;
        }

        ofstream file(filename, ios::app); // Άνοιγμα για προσθήκη 

        // Αν δεν ανοιξει το αρχειο τοτε τερματιζει η συναρτηση
        if (!file.is_open()) {
            cout << "Error: Cannot open file " << filename << endl;
            return;
        }

        // Αποθήκευση παραγγελίας
        file << "---CART " << cart_number << " START---\n";
        for (vector<Item>::iterator it = items.begin(); it != items.end(); ++it) {
            file << it->quantity << " " << it->product.getTitle() << endl;
        }
        file << "---CART " << cart_number << " END---\n";
        file << "Total Cost: " << totalCost << endl;
        file << endl;
        file.close();

    }
};

// κλαση χρηστη 
class User{
protected:
    string username;    // ονομα του χρηστη 
    string password;    // κωδικος χρηστη 
    bool isAdmin;       // επιλογη για το αν ειναι admin ή πελατης
public: 
    // constructor της κλασης user
    User(string n, string psw, bool admin): username(n), password(psw), isAdmin(admin){cout << "User created.\n";}
    // συναρτηση για συνδεση του χρηστη
    bool login(const string &n,const string &psw) const{
        return username == n && password == psw;
    }

    // συναρτηση για επιστροφη ονοματος του χρηστη
    string getUsername() const { return username; }

    // συναρτηση για να ελεγχω αν υπαρχει ηδη ο χρηστης στο αρχειο
    bool fuctionsearch(const string& filename, const string& username) {
        ifstream file("files/users.txt"); 
        string line;
        while (getline(file, line)) {
            if (line.find(username)!= string::npos) {
                return true; // υπαρχει
            }
        }
        return false; // δεν υπαρχει 
    }
    
    virtual ~User(){} // virtual destructor
};

// κλαση Admin που κληρονομειται απο την User
class Admin: public User{
public:
    // consrtuctor της admin
    Admin(string n, string psw):User(n, psw, true){}
    string getRole() const { return "Admin"; }

    // συναρτηση για εμφανιση των επιλογων που εχει ο Admin
    void displayOptions() {
        cout << "Welcome, " << getUsername() << endl;
        cout << "---Admin Menu---" << endl;
        cout << "Here are your options:" << endl;
        cout << "1. View all products" << endl;
        cout << "2. Add a new product" << endl;
        cout << "3. Edit a product" << endl;
        cout << "4. Search for a product" << endl;
        cout << "5. View out of stock products" << endl;
        cout << "6. View Best Seller products" << endl;
        cout << "7. Exit" << endl;
    }
    
    //  συναρτηση για εμφανιση ολων των προιοντων 
    void viewAllProducts( vector<Product>& products) {
       for(Product& p : products) { 
           p.DisplayProductInfo();  // εμφανιση χαρακτηριστικων του προιοντος 
           cout << endl;
       }
   }

    // συναρτηση για προσθηκη ενος προιοντος(με ολα τα χαρακτηριστικα του) στο καταστημα 
    void addProduct(vector<Product>& products) {
        cout << "Enter the title of the new product: ";
        string title;
        cin.ignore();
        getline(cin, title);
        cout << "Enter the description of the new product: ";
        string description;
        // cin.ignore(); // Add this line to clear the input buffer
        getline(cin, description);
        cout << "Enter the category of the new product: ";
        string category;
        cin >> category;
        cout << "Enter the subcategory of the new product: ";
        string subcategory;
        cin >> subcategory;
        cout << "Enter the price of the new product: ";
        float price;
        cin >> price;
        cout << "Enter the unit type(units/kg) of the new product: ";
        string unitType;
        cin >> unitType;
        cout << "Enter the quantity of the new product: ";
        float quantity;
        cin >> quantity;
        products.push_back(Product(title, description, category, subcategory, price, unitType, quantity));  //  προσθηκη στο vector με τα διαθεσιμα προιοντα 
        ofstream fileOut("files/products.txt", ios::app);   // εγγραφη αρχειου 
        if (fileOut.is_open()) {    // ανοιγμα αρχειου 
            fileOut << endl << title << " @ " << description << " @ " << category << " @ " << subcategory << " @ " << price << " @ " << unitType << " @ " << quantity;
            cout << "Product added successful!" << endl;
        } else {    // σε περιπτωση που δεν ανοιξει το αρχειο 
            cout << "Error opening file!" << endl;
        }
        cout << endl;
    }

    // συανρτηση για αλλαγη ενος χαρακτηριστικου απο ενα προιον
    void changeProduct(vector<Product>& products) {
        int choise;
        cout << "Enter the title of the product you want to edit: ";
        string title;
        cin.ignore();
        getline(cin, title);
            for(Product& p : products){     // αναζητηση του στοιχειου 
                if(p.getTitle() == title){
                    cout << "What do you want to change on " << title << "?" << endl;
                    cout << "1. Description" << endl;
                    cout << "2. Price" << endl;
                    cout << "3. Quantity" << endl;
                    cin >> choise;      // επιλογη για το τι θελω να αλλαξω
                    switch (choise) {
                        case 1:
                            {
                            cout << "Enter the new description: ";
                            string newDescription;
                            cin.ignore();
                            getline(cin, newDescription);
                            p.setDescription(newDescription);
                            cout << "Product description edited successfully." << endl;
                            break;;
                            }
                        case 2:
                            {
                            cout << "Enter the new price: ";
                            float newPrice;
                            cin >> newPrice;
                            p.setPrice(newPrice);
                            cout << "Product price edited successfully." << endl;
                            break;
                            }
                        case 3:
                            {
                            cout << "Enter the new quantity: ";
                            float newQuantity;
                            cin >> newQuantity;
                            p.setQuantity(newQuantity);
                            cout << "Product quantity edited successfully." << endl;
                            break;;
                            }
                        default:
                            cout << "Invalid option." << endl;
                    }
                    // Save updated products to file
                    saveProductsToFile("files/products.txt", products);
                    return;
                }
            }
            // αν δεν βρεθει το προιον
            cout << "Product not found." << endl;
    }
    // συναρτηση για αναζητηση ενος προιοντος σε ενα vector με προιοντα με βαση τον τιτλο του ή την κατηργορια ή  την υποκατηργορια
    void searchProduct(vector<Product>& products){
        int choise;
        cout << "You want to search for products by:" << endl;
        cout << "1. Title" << endl;
        cout << "2. Category" << endl;
        cout << "3. Subcategory" << endl;
        cin >> choise;
        bool found = false;
        switch (choise) {
            // με βαση το τιτλο του 
            case 1:
                {
                cout << "Enter the title of the product:" << endl;
                string title_;
                cin.ignore();
                getline(cin, title_);
                for(Product p : products){
                    if(p.getTitle() == title_){
                        found = true;
                        p.DisplayProductInfo();
                        cout << endl;
                        break;
                    }
                }
                // αν δεν βρεθει
                if(!found){
                    cout << "Product coudn't be found!" << endl;
                }
                break;
                }
                // με βαση την κατηργορια του
            case 2:
                {
                cout << "Enter the category name:" << endl;
                string category_;
                cin >> category_;
                for(Product p : products){
                    if(p.getCategory() == category_){
                        found = true;
                        p.DisplayProductInfo();
                        cout << endl;
                    }
                    // αν δεν βρεθει
                    if(!found){
                        cout << "No products found in this category!" << endl;
                    }
                }
                break;
                }
                // με βαση την υποκατηγορια του
            case 3:
                {
                cout << "Enter the subcategory  name:" << endl;
                string subcategory_;
                cin >> subcategory_;
                for(Product p : products){
                    if(p.getSubcategory() == subcategory_){
                        found = true;
                        p.DisplayProductInfo();
                        cout << endl;
                    }
                    // αν δεν βρεθει 
                    if(!found){
                        cout << "No products found in this subcategory!" << endl;
                    }
                }
                break;
                }
                // οποιαδηποτε αλλη επιλογη απο τις παραπανω 
            default:
                {
                cout << "Wrong option!" << endl;
                break;
                }
        }

                

    }
    // συναρτηση που εμφανιζει τα προιοντα που εξαντληθηκαν 
    void viewOutOfStockProducts(vector<Product>& products) const {
        cout << "Out of stock products : " << endl;
        for(Product& p : products){
            // αν η ποσοτητα ειναι μηδεν τοτε εμφανιζει τα προιοντα με τα χαρακτηριστικα τους
            if(p.getQuantity() == 0){
                p.DisplayProductInfo();
                cout << endl;
            }
        }
    }
  
     // εμαφανιση των κορυφαιων 5 προιοντων 
    void viewBestSellingProducts(vector<Product>& products){
     ////////////////////////////////////////////////////////////////   
       sort(products.begin(), products.end(), CompareBySold());

       
        cout << "Top 5 Best-Selling Products:" << endl;
        for (size_t i = 0; i < 5 && i < products.size(); ++i) {
            products[i].DisplayProductInfo();
            cout << endl;
        }        
    }

    // συναρτηση για τις επιλογες του διαχειρηστη
    void menu(vector<Product>& products) {
        int choise = 0; // μεταβλητη επιλογων
        do {
            displayOptions();
            cin >> choise; // πληκτολογει ο διαχειρηστης την επιλογη του
            switch (choise) {
                case 1:
                    viewAllProducts(products);  // εμαφνιση ολων των προιοντων του καταστηματος
                    break;
                case 2:
                    addProduct(products);   // προσθηκη νεου προιοντος 
                    break;
                case 3:
                    changeProduct(products);    // αλλλαγη προιοντος 
                    break;
                case 4:
                    searchProduct(products);    // αναζητηση προιοντος 
                    break;
                case 5:
                    viewOutOfStockProducts(products);   // εμφανιση εξαντλημενων προιοντων
                    break;
                case 6:
                    viewBestSellingProducts(products);  // τα 5 κορυφαια προιοντα 
                    break;
                case 7:
                    cout << "Goodbye!\n";   // εξοδος
                    return;
                default:    // περιπτωση που επιλεχθηκε καποια αλλη επιλογη
                    cout << "Invalid choice, please try again.\n";
            }
        } while (choise != 7); // ο παραπανω βροχος συνεχιζεται μεχρις οτου ο δαιχειρηστης να πληκτρολογησει την επιλογη 7
    }

};

// κλαση για τον πελατη που κληρονομειται απο την User
class Customer : public User{
private:
    Cart personal_cart; // αντικειμενον της κλασης Cart που απεικονιζει το προσωπικο του καλαθι
    
public:
     // constructor της καλσης 
    Customer(string n, string psw):User(n, psw, false){
        personal_cart.setCartOwner(n);
    }
    string getRole() const { return "Customer"; }

    // συναρτηση για τις επιλογες του πελατη 
    void displayOptions() {
        cout << "Welcome " << getUsername() << " !" << endl;
        cout << "Here are your options:" << endl;
        cout << "1. Search for a product" << endl;
        cout << "2. Add a product to your cart" << endl;
        cout << "3. Remove a product from your cart" << endl;
        cout << "4. CHECKOUT" << endl;
        cout << "5. Order history" << endl;
        cout << "6. Exit" << endl;
    }

    // συναρτησ για αναζητηση ενος προιοντος 
    void searchProduct(vector<Product>& products){
        int choise; 
        cout << "You want to search for products by:" << endl;
        cout << "1. Title" << endl;
        cout << "2. Category" << endl;
        cout << "3. Subcategory" << endl;
        cin >> choise;
        bool found = false;
        switch (choise) {
            // αναζητηση ανα τον τιτλο
            case 1:
                {
                cout << "Enter the title of the product:" << endl;
                string title_;
                cin >> title_;
                for(Product p : products){
                    if(p.getTitle() == title_){
                        found = true;
                        p.DisplayProductInfo();
                        cout << endl;
                        break;
                    }
                }
                // αν δεν βρεθει
                if(!found){
                    cout << "Product coudn't be found!" << endl;
                }
                break;
                }
            // αναζητηση ανα την κατηγορια
            case 2:
                {
                cout << "Enter the category name:" << endl;
                string category_;
                cin >> category_;
                for(Product p : products){
                    if(p.getCategory() == category_){
                        found = true;
                        p.DisplayProductInfo();
                        cout << endl;
                    }
                    // αν δεν βρεθει
                    if(!found){
                        cout << "No products found in this category!" << endl;
                    }
                }
                break;
                }
            // αναζητηση ανα την υποκατηγορια
            case 3:
                {
                cout << "Enter the subcategory  name:" << endl;
                string subcategory_;
                cin >> subcategory_;
                for(Product p : products){
                    if(p.getSubcategory() == subcategory_){
                        found = true;
                        p.DisplayProductInfo();
                        cout << endl;
                    }
                    // αν δεν βρεθει 
                    if(!found){
                        cout << "No products found in this subcategory!" << endl;
                    }
                }
                break;
                }
            // αν επιλεχθει λαθος επιλογη
            default:
                {
                cout << "Wrong option!" << endl;
                break;
                }
        }
    }
    // προσθηκη ενος προιοντος στο προσωπικο καλαθι 
    void addProduct(vector<Product>& products){
        cout << "Product's title you want to add!" << endl;
        string title;
        cin.ignore();
        getline(cin, title);
        for(Product& p : products){
            if(p.getTitle() == title){  // αν βρεθει στο καταστημα ο τιτλος του προιοντος
                cout << "Enter the quantity you want to add: ";
                int quantity;
                cin >> quantity; // πληκτρολογει την ποσοτητα
                p.setQuantity(p.getQuantity() - quantity);  // αλλαγη της ποσοτητας
                personal_cart.addItem(p, quantity); // προσθηκη το καλαθη
                saveProductsToFile("files/products.txt", products); // ενημερωση αρχειου
                p.setSold(p.getSold() + quantity);  // προσθηκη και της συνολικης ποσοτητας
                return;
            
            }
        }
        cout << "Product not found!" << endl;// αν δεν βρεθει
    }

    // συναρτηση για αφαιρεση ενος προιοντος απο το καλαθι
    void removeProduct(vector<Product>& products){
        cout << "Product's title you want to remove!" << endl;
        string title;
        cin >> title;   // πληκτρολογει τον τιτλο του προιοντος που θελει να αφαρεθει
        for(Product& p : products){
            // αν βρεθει
            if(p.getTitle() == title){
                cout << "Enter the quantity you want to remove: ";
                int quantity;
                cin >> quantity;    // πληκτρολογει την ποσοτητα
                p.setQuantity(p.getQuantity() + quantity);  // αλλαγη της ποστητας 
                cout << "Product's left quantity is: " << p.getQuantity() << endl;
                personal_cart.removeItem(p, quantity);  // αφαιρεση
                saveProductsToFile("files/products.txt", products); // ενημερωση αρχειου
                p.setSold(p.getSold() -quantity);   // αφαιρεση απο ολο το συνολο των προιοντων
                return;
            }
        }
    }

    // συναρτηση για πληρωμη
    void checkout(){
        personal_cart.checkout();   // μεταφεραται στην κλαση Cart για πληρωμη
        personal_cart.cart_number++;    // αυξανεται και το πληθος των καλαθιων
    }

    // συναρτηση γιας τις επιλογες του πελατη    
    void menu(vector<Product>& products) {
        int choise = 0; // Declare choise here
        do {
            displayOptions();   //συναρτηση για εμφανιση των επιλογων 
            cin >> choise; // πληκτρολογει ο πελατης την επιλογη του
            switch (choise) {
                case 1:
                    searchProduct(products);    // αναζητηση προιοντος 
                    break;
                case 2:
                    addProduct(products);    // προσθηκη προιοντος
                    break;
                case 3:
                    removeProduct(products);    // αφαιρεση προιοντος
                    break;
                case 4:
                    checkout();     // πληρωμη παραγγελιας
                    break;
                case 5:
                    view_order_history();   // εμφανιση ιστορικου παραγγελιων 
                    break;
                case 6:
                    cout << "Goodbye!\n";   // εξοφος απο το menu
                    return;
                default:
                    cout << "Invalid choice, please try again.\n";
            }
        } while (choise != 6); // ο βροχος αυτος συνεχιζεται μεχρις οτου ο πελατης να επιλεξει την επιλογη 6
    }

    // συναρτηση για το ιστορικο παραγγελιων 
    void view_order_history() {
        // συνταξη του filepath με το ονομα του πελατη
        string filename = "files/order_history/" + username + "_history.txt";
        // ανοιγμα αχρειου για αναγνωση
        ifstream file(filename);
        cout << "Order history for user: " << username << endl;
        // Αν δεν ανοιξει 
        if (!file.is_open()) {
            cout << "No order history found for user: " << username << endl;
            return;
        }

        // Ανάγνωση και εμφάνιση περιεχομένων αρχείου
        string line;
        while (getline(file, line)) {
            cout << line << endl;
        }
        cout << endl;
        file.close();
    }
};

void signup (string username, string password, bool isAdmin) {

    // Έλεγχος αν το username υπάρχει ήδη
    ifstream file("files/users.txt"); 
    string line;
    while (getline(file, line)) {
        if (line.find(username) != string::npos) {
            cout << "Username already exists. Please choose another one." << endl;
            return;
        }
    }
    // Δημιουργία νέου χρήστη
    User newUser(username, password, isAdmin);

    // Αποθήκευση του username
    ofstream fileOut("files/users.txt", ios::app);
    if (fileOut.is_open()) {
        fileOut << "Username: " << username << ", password: " << password << " " << isAdmin << endl;
        cout << "Signup successful!" << endl;
    } else {
        cout << "Error opening file!" << endl;
    }
}

// συναρτηση για συνδεσει του χρηστη
int login(string username, string password) {
    // αναγνωση αρχειου
    ifstream file("files/users.txt");
    // αν δεν ανοιξει
    if (!file) {
        cout << "Error: Unable to open users file." << endl;
        return 0;
    }

    string line;
    while (getline(file, line)) {
        string storedUsername, storedPassword;

        // βρισκει την θεση του πρωτου κομματος
        size_t passwordPos = line.find(",");
        // αν δεν βρεθει
        if (passwordPos != string::npos) {
            // αποθηκευει το ονομα
            storedUsername = line.substr(0, passwordPos);
            // αποθηκευει τον κωδικο 
            storedPassword = line.substr(passwordPos + 1, line.length() - (passwordPos + 1) - 2);
            // αποθηκευει την επιλογη για το αν ειναι admin ή πελατης
            int storedIsAdmin = line.back() - '0';
            // αφαιρεση των κενων που μπορει να υπαρχουν στο τελος ή στη αρχη των παρακατω συμβολοσειρων
            storedUsername.erase(storedUsername.find_last_not_of(" \t\n\r") + 1);

            // Ελεγχω αν μπορει να συνδεθει ο πελατης 
            if (storedUsername == username) {
                if (storedPassword == password) {
                    cout << "You are logged in!" << endl;                   
                    return 1; // Επιτυχης συνδεση
                } else {
                    cout << "Wrong password! Please try again." << endl;
                    return 0; // λανθασμενη περιπτωση
                }
            }
        }
    }
    // Δεν βρεθηκε το ονομα
    cout << "Username not found! Please try again." << endl;
}

// συναρτηση για ελεγχω αν ο χρηστης ειναι admin ή οχι
int isAdminCheck(string username, string password) {
    // τα δεδομενα βρισκονται στο users.txt
    ifstream file("files/users.txt");
    if (!file) {
        cout << "Error: Unable to open users file." << endl;
        return 0;
    }

    string line;
    while (getline(file, line)) {
        string storedUsername, storedPassword;

        // δεικτης κωδικου
        size_t passwordPos = line.find(",");
        // αν βρεθει ο δεικτης
        if (passwordPos != string::npos) {
            // ονομα του χρηστη
            storedUsername = line.substr(0, passwordPos);
            // κωδικος του χρηστη
            storedPassword = line.substr(passwordPos + 1, line.length() - (passwordPos + 1) - 2);
            // αποθηκευση γαι το αν ειναι admin ή οχι 
            int storedIsAdmin = line.back() - '0';
            // αφαιρεση των κενων που μπορει να υπαρχουν στο τελος ή στη αρχη της παρακατω συμβολοσειρας
            storedUsername.erase(storedUsername.find_last_not_of(" \t\n\r") + 1);

            // Αν δωθει σωστο ονομα σε σχεση με αυτο που βρισκεται στο αρχειο 
            if (storedUsername == username) {
                    if(storedIsAdmin == 1) {
                        return 1; // ειναι admin
                    } else {
                        return 0; // δεν ειναι admin
                    }
            }
        }
    }
    
    // Το ονομα δεν βρεθηκεβ
    cout << "Username not found! Please try again." << endl;
}

// Συναρτηση για την εναρξη του eshop
void startmenu(vector<Product>& products){
    cout << "Welcome to the e-shop!!!" << endl;
    cout << "Do you want to login or register? (enter option):" << endl;
    cout << "1. Login" << endl;
    cout << "2. Register" << endl;
    int choice;
    string username, password;
    bool isAdmin=false;
    cin >> choice;  // πληκτρολογει ο χρηστης την επιλογη του
    switch (choice) {
        // συνδεση 
        case 1:
            cout << "Enter username: "; 
            cin.ignore();   // αφαιρεση των κενων
            getline (cin, username);

            cout << "Enter password: ";
            getline (cin, password);


            if(login(username, password)){
                cout << isAdminCheck(username, password) << endl;
                // Αν ειναι admin τοτε δημιουργει ενα αντικειμενο Admin 
                if(isAdminCheck(username, password) == 1) {
                    Admin admin(username, password);
                    // μπαινει στο menu του admin
                    admin.menu(products);
                // αλλιως ειναι costumer και δημιουργει ενα αντικειμενο costumer
                } else {
                    Customer customer(username, password);
                    // μπαινει στο menu του costumer
                    customer.menu(products);
                }
            }
            break;
        // εγγραφη
        case 2:
            cout << "Enter username: ";
            cin.ignore();
            getline (cin, username);

         
            cout << "Enter password: ";
            getline (cin, password);

            // αν δεν δοθηκε κωδικος
            if (password.empty()) {
                cout << "Password is required." << endl;
                return;
            }

            cout << "Is the user an admin (0 for No, 1 for Yes): ";
            cin >> isAdmin; // πληκτρολογει ο user αν ειναι admin ή οχι
            cin.ignore(); // με συνάρτηση αγνόω το κενό που αφήνει το enter μετά την εισαγωγή του αριθμού

            // συναρτηση για δημιουργια λογαριασμου
            signup(username, password, isAdmin);
            break;
        // οποιαδηποτε αλλη επιλογη 
        default:
            cout << "Invalid choice, please try again.\n";
            break;
    }
}

// static μετρητης καλαθιων 
int Cart::cart_number = 1;



// συναρτηση για διαβασμα των προιοντων απο το αρχειο και προσθηκη στο vector 
void loadProductsFromFile(const string& filename, vector<Product>& products) {
    // αναγνωση αρχειου
    ifstream file(filename);
    // σν δεν ανοιξει το αρχειο
    if (!file.is_open()) {
        cout << "Failed to open file: " << filename << endl;
        return;
    }

    string line;    // αποθηκευση καθε γραμμης απο το αρχειο
    while (getline(file, line)) {
        stringstream ss(line);  // για επεξεργασια δεδομενων
        string title, description, category, subcategory, unit;
        double price;
        int quantity;
        // καθε πεδιο του προιοντος το χωριζω με @, επισης με την συναρτηση trim αφαιρουνται τα κενα διαστηματα
        getline(ss, title, '@');
        trim(title);
        getline(ss, description, '@');
        trim(description);
        getline(ss, category, '@');
        trim(category);
        getline(ss, subcategory, '@');
        trim(subcategory);
        // διαβαζει την τιμη του προιοντος απο το stringstream
        ss >> price;
        ss.ignore(1, '@');

        // επαναφορα του stringstream για αποφυγει σφαλαμτων
        ss.clear();
        ss.ignore(numeric_limits<streamsize>::max(), '@'); // αγνοει ολα τα περιττα δεδομενα μεχρι να συναντησει το @
        // διαβαζει την μοναδα μετρησης του προιοντος 
        getline(ss, unit, '@');
        // αφαιρεση κενων
        trim(unit);
        cout << unit << " is the unit" << endl;
        ss >> quantity;

        // δημιουργια του προιοντος 
        Product product(title, description, category, subcategory, price, unit, quantity);
        products.push_back(product);    // προσθηκη στο vector των προιοντων
    }
    // κλεισιμο αρχειου
    file.close();
}

int main() {
    vector <Product> products;  // αρχικοποιηση vector των προιοντων

    // εισαγωγη των προιοντων απο το αρχειο στο vector 
    loadProductsFromFile("files/products.txt", products);
    
    // εναρξη του eshop
    startmenu(products);

    return 0;
}
