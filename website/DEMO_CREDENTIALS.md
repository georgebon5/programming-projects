# 🔑 DEMO CREDENTIALS - HelpMeAnytime 2.0

## 👤 DEMO ACCOUNTS

### 1. Πολίτης (Citizen)
```
Email: citizen@helpmeanytime.gr
Password: Demo123!
Όνομα: Γιώργος Παπαδόπουλος
Τηλέφωνο: 210 123 4567
Role: citizen
```

**Τι μπορεί να κάνει:**
- ✅ Κλείσιμο ραντεβού με επαγγελματίες
- ✅ Δημιουργία αιτημάτων βοήθειας
- ✅ Εθελοντισμός σε αιτήματα
- ✅ Πρόταση έργων
- ✅ Pledges σε έργα

---

### 2. Επαγγελματίας (Professional)
```
Email: professional@helpmeanytime.gr
Password: Demo123!
Όνομα: Νίκος Ηλεκτρολόγος
Τηλέφωνο: 210 234 5678
Role: professional
Επάγγελμα: Ηλεκτρολόγος
```

**Τι μπορεί να κάνει:**
- ✅ Δει τα ραντεβού του
- ✅ Ενημέρωση status ραντεβού
- ✅ Προφίλ με ratings
- ✅ Διαθεσιμότητα

---

### 3. Υπάλληλος Δήμου (Municipality Admin)
```
Email: admin@athens.gov.gr
Password: Admin123!
Όνομα: Μαρία Δημητρίου
Τηλέφωνο: 210 345 6789
Role: municipality
Department: Υπηρεσία Πολιτών
```

**Τι μπορεί να κάνει:**
- ✅ Έγκριση/απόρριψη ραντεβού
- ✅ Διαχείριση επαγγελματιών
- ✅ Στατιστικά & analytics
- ✅ Διαχείριση έργων
- ✅ Budget monitoring

---

## 🔧 QUICK TEST LOGIN

### Για γρήγορο testing χρησιμοποίησε:

#### Πολίτης:
```
📧 citizen@helpmeanytime.gr
🔒 Demo123!
```

#### Admin:
```
📧 admin@athens.gov.gr
🔒 Admin123!
```

---

## 🧪 TEST SCENARIOS

### Scenario 1: Κλείσιμο Ραντεβού
1. Login ως **citizen@helpmeanytime.gr**
2. Dashboard → "Κλείσε Ραντεβού"
3. Επίλεξε "Γιάννης Παπαδόπουλος - Ηλεκτρολόγος"
4. Διάλεξε ημερομηνία αύριο
5. Ώρα: 10:00
6. Εκτιμώμενες ώρες: 3h
7. Διεύθυνση: "Ακαδημίας 123, Αθήνα"
8. Τηλέφωνο: 210 123 4567
9. Περιγραφή: "Επισκευή ηλεκτρικού πίνακα"
10. **Παρατήρησε το cost calculator:**
    - €50/ώρα × 3 ώρες = €150
    - Επιδότηση 70% = -€105
    - **Πληρώνεις: €45** (αντί για €150!)
11. Submit
12. ✅ Success screen → Redirect στο `/bookings`

---

### Scenario 2: Αίτημα Βοήθειας (Ζητάω Βοήθεια)
1. Login ως **citizen@helpmeanytime.gr**
2. Dashboard → "Ζήτα Βοήθεια"
3. Επίλεξε κατηγορία: "💻 Τεχνολογία"
4. Περιγραφή: "Χρειάζομαι βοήθεια να στήσω το WiFi μου"
5. Επείγον: Μέτρια
6. Τοποθεσία: "Κολωνάκι"
7. Προτιμώμενη ημερομηνία: Σήμερα ή αύριο
8. Τηλέφωνο: 210 123 4567
9. Submit
10. ✅ Success screen → Redirect στο `/help`

---

### Scenario 3: Εθελοντισμός (Προσφέρω Βοήθεια)
1. Login ως **citizen@helpmeanytime.gr** (ή δημιούργησε νέο account)
2. `/help` → Δες ανοιχτά αιτήματα
3. Βρες ένα που σε ενδιαφέρει (π.χ. "Τεχνολογία")
4. Click **"💙 Θέλω να Βοηθήσω"**
5. ✅ Success! Τώρα έχεις τα στοιχεία επικοινωνίας

---

### Scenario 4: Browse Professionals
1. Δεν χρειάζεται login!
2. `/professionals` → Δες όλους τους επαγγελματίες
3. Φίλτρα ανά επάγγελμα (Ηλεκτρολόγος, Υδραυλικός, κλπ)
4. Δες ratings, τιμές, experience
5. Click "Book Appointment" για login/signup

---

### Scenario 5: Municipality Dashboard (TODO)
1. Login ως **admin@athens.gov.gr**
2. `/municipality` → Dashboard
3. Δες pending bookings
4. Approve/Reject
5. Στατιστικά & reports

---

## 🗄️ MOCK DATA ΠΟΥ ΕΧΟΥΜΕ

### Professionals (3):
```javascript
1. Γιάννης Παπαδόπουλος
   - Επάγγελμα: Ηλεκτρολόγος
   - Rating: 4.8/5
   - Τιμή: €50/ώρα → €15/ώρα (με επιδότηση)
   - Experience: 15 years
   - Areas: Κέντρο Αθήνας, Πειραιάς, Νότια Προάστια

2. Μαρία Γεωργίου
   - Επάγγελμα: Υδραυλικός
   - Rating: 4.9/5
   - Τιμή: €45/ώρα → €13.50/ώρα
   - Experience: 12 years
   - Areas: Βόρεια Προάστια, Κηφισιά, Μαρούσι

3. Δημήτρης Αντωνίου
   - Επάγγελμα: Μαραγκός
   - Rating: 4.7/5
   - Τιμή: €40/ώρα → €12/ώρα
   - Experience: 20 years
   - Areas: Όλη η Αττική
```

### Bookings (2):
```javascript
1. Booking #1
   - Citizen: demo-user-1
   - Professional: Γιάννης (Ηλεκτρολόγος)
   - Status: pending
   - Date: 2025-11-20, 10:00
   - Hours: 3h
   - Cost: €150 → €45 (citizen pays)
   - Address: Ακαδημίας 45, Αθήνα

2. Booking #2
   - Citizen: demo-user-2
   - Professional: Μαρία (Υδραυλικός)
   - Status: approved
   - Date: 2025-11-18, 14:00
   - Hours: 2h
   - Cost: €90 → €27 (citizen pays)
   - Address: Κηφισίας 123, Μαρούσι
```

### Help Requests (3):
```javascript
1. Μετακόμιση
   - Category: moving
   - Urgency: high
   - Location: Κολωνάκι
   - Description: "Βοήθεια με μεταφορά επίπλων"
   - Status: open

2. Τεχνολογία
   - Category: technology
   - Urgency: medium
   - Location: Καλλιθέα
   - Description: "Χρειάζομαι βοήθεια με laptop"
   - Status: open

3. Συντροφιά
   - Category: companionship
   - Urgency: low
   - Location: Νέος Κόσμος
   - Description: "Αναζητώ κάποιον για καφέ"
   - Status: open
```

---

## 🎯 TESTING CHECKLIST

### Frontend Pages:
- [ ] `/` - Landing page
- [ ] `/auth` - Login/Signup
- [ ] `/dashboard` - User dashboard
- [ ] `/professionals` - Professionals list ✨
- [ ] `/bookings/new` - Book appointment ✨
- [ ] `/bookings` - My bookings ✨
- [ ] `/help` - Help requests ✨
- [ ] `/help/new` - New help request ✨
- [ ] `/projects` - Projects list (TODO)
- [ ] `/municipality` - Admin dashboard (TODO)

### Features to Test:
- [ ] Signup με email
- [ ] Login με credentials
- [ ] Logout
- [ ] Browse professionals (χωρίς login)
- [ ] Book appointment (με login)
- [ ] Real-time cost calculator
- [ ] View my bookings
- [ ] Filter bookings by status
- [ ] Browse help requests
- [ ] Create help request
- [ ] Volunteer for help request
- [ ] Filter help by category
- [ ] Navigation menu
- [ ] Mobile responsive
- [ ] Loading states
- [ ] Success messages
- [ ] Error handling

---

## 💡 TIPS

### Για Development:
1. **Δεν χρειάζεται πραγματικό Supabase** - όλα τρέχουν με mock data
2. **Mock auth**: Οποιοδήποτε email/password θα δουλέψει (για τώρα)
3. **Refresh δεν χάνει data** - τα mock data είναι hardcoded
4. **LocalStorage**: Το auth state αποθηκεύεται locally

### Για Testing:
- **Chrome DevTools** → Responsive mode για mobile testing
- **Console** για API calls debugging
- **Network tab** για requests/responses
- **Clear localStorage** αν κολλήσεις: `localStorage.clear()`

### Keyboard Shortcuts:
- `Cmd+R` - Refresh
- `Cmd+Shift+R` - Hard refresh
- `Cmd+Option+I` - DevTools
- `Cmd+Shift+M` - Mobile view

---

## 🚀 QUICK START

```bash
# 1. Start server (αν δεν τρέχει ήδη)
cd /Users/sotirioslympakis/Desktop/helpmeanytime
npm run dev

# 2. Open browser
# http://localhost:3002

# 3. Login με:
# citizen@helpmeanytime.gr / Demo123!

# 4. Explore! 🎉
```

---

## 🐛 TROUBLESHOOTING

### "Port already in use"?
```bash
# Kill process on port
lsof -ti:3002 | xargs kill -9

# Restart
npm run dev
```

### "Cannot connect to Supabase"?
**Φυσιολογικό!** Χρησιμοποιούμε mock data για τώρα.

### Logout δεν δουλεύει?
```javascript
// Open console και γράψε:
localStorage.clear()
location.reload()
```

### Stuck στο loading?
**Refresh τη σελίδα** - κάποιο API call μπορεί να αποτύχει.

---

## 📞 SUPPORT

Για οποιοδήποτε πρόβλημα:
1. Check console για errors
2. Check Network tab για failed requests
3. Clear localStorage & refresh
4. Restart dev server

---

## 🎉 ENJOY TESTING!

Το **HelpMeAnytime 2.0** περιμένει το test σου! 🚀

**Current Status**: ✅ All systems operational
**Mock Data**: ✅ Ready
**Server**: ✅ Running on http://localhost:3002
**Ready for**: 🏆 Apps4Athens 2025 Demo

---

**Last Updated**: November 15, 2025
**Version**: 2.0.0
**Status**: 🚀 Ready for Testing!
