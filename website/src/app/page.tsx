'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useEffect } from 'react'

export default function Home() {
  const router = useRouter()
  const { user, isAuthenticated, signOut } = useAuth()

  // If user is authenticated, show different navigation
  const handleSignOut = async () => {
    await signOut()
    // Stay on homepage after logout
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-gray-900">
                HelpMeAnytime
              </span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-700 hover:text-blue-600 transition">Υπηρεσίες</a>
              <a href="#how-it-works" className="text-gray-700 hover:text-blue-600 transition">Πώς Λειτουργεί</a>
              <a href="#about" className="text-gray-700 hover:text-blue-600 transition">Σχετικά</a>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-gray-700">
                    <strong>{user?.name || user?.email}</strong>
                  </span>
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="px-6 py-2 bg-blue-900 text-white rounded-lg hover:bg-blue-800 transition shadow-md font-semibold"
                  >
                    Dashboard
                  </button>
                  <button
                    onClick={handleSignOut}
                    className="text-gray-700 hover:text-red-600 transition font-medium"
                  >
                    Αποσύνδεση
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => router.push('/auth?mode=signin')}
                    className="text-gray-700 hover:text-blue-600 transition"
                  >
                    Σύνδεση
                  </button>
                  <button
                    onClick={() => router.push('/auth?mode=signup')}
                    className="px-6 py-2 bg-blue-900 text-white rounded-lg hover:bg-blue-800 transition shadow-md font-semibold"
                  >
                    Εγγραφή
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Συνδέοντας τη
              <span className="block text-blue-600 mt-2">
                Κοινότητα της Αθήνας
              </span>
            </h1>
            <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
              Μια ολοκληρωμένη πλατφόρμα που συνδέει δημότες, εθελοντές, επαγγελματίες και δήμο 
              για καλύτερες υπηρεσίες και συνεργατικά έργα.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => router.push('/auth')}
                className="px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition shadow-lg"
              >
                Ξεκίνα Τώρα
              </button>
              <button
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="px-8 py-4 bg-white text-blue-600 text-lg font-semibold rounded-lg hover:bg-gray-50 transition shadow-lg border-2 border-blue-200"
              >
                Μάθε Περισσότερα
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              3 Τρόποι να Βοηθήσεις την Κοινότητα
            </h2>
            <p className="text-xl text-gray-600">
              Επίλεξε τον τρόπο που σου ταιριάζει περισσότερο
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1: Bookings */}
            <div className="bg-white rounded-xl p-8 shadow-lg border hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-blue-900">📅</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Κλείσε Ραντεβού με Ειδικό
              </h3>
              <p className="text-gray-600 mb-6 text-base">
                Ηλεκτρολόγοι, υδραυλικοί και άλλοι ειδικοί με επιδότηση από τον δήμο. 
                Πληρώνεις μόνο μια μικρή τιμή!
              </p>
              <ul className="space-y-2 text-base text-gray-600 mb-6 text-left max-w-xs mx-auto">
                <li>• Ηλεκτρολόγοι</li>
                <li>• Υδραυλικοί</li>
                <li>• Μαραγκοί</li>
                <li>• Βαφείς & πολλά άλλα</li>
              </ul>
              <button
                onClick={() => router.push('/professionals')}
                className="w-full px-6 py-3 bg-blue-900 text-white rounded-lg hover:bg-blue-800 transition font-semibold text-base"
              >
                Κλείσε Ραντεβού
              </button>
            </div>

            {/* Feature 2: Help Requests */}
            <div className="bg-white rounded-xl p-8 shadow-lg border hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-green-700">🆘</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Ζήτα ή Προσφέρε Βοήθεια
              </h3>
              <p className="text-gray-600 mb-6 text-base">
                Χρειάζεσαι βοήθεια; Δημιούργησε αίτημα και εθελοντές κοντά σου θα σε βοηθήσουν δωρεάν!
              </p>
              <ul className="space-y-2 text-base text-gray-600 mb-6 text-left max-w-xs mx-auto">
                <li>• Μετακόμιση</li>
                <li>• Ψώνια</li>
                <li>• Τεχνολογία</li>
                <li>• Συντροφιά & άλλα</li>
              </ul>
              <button
                onClick={() => router.push('/help/new')}
                className="w-full px-6 py-3 bg-green-700 text-white rounded-lg hover:bg-green-600 transition font-semibold text-base"
              >
                Ζήτα Βοήθεια
              </button>
            </div>

            {/* Feature 3: Civic Projects */}
            <div className="bg-white rounded-xl p-8 shadow-lg border hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-purple-700">🏗️</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Πρότεινε Έργα
              </h3>
              <p className="text-gray-600 mb-6 text-base">
                Πρότεινε έργα για την περιοχή σου και συγκέντρωσε υποστήριξη από άλλους δημότες!
              </p>
              <ul className="space-y-2 text-base text-gray-600 mb-6 text-left max-w-xs mx-auto">
                <li>• Πάρκα & Πράσινο</li>
                <li>• Υποδομές</li>
                <li>• Πολιτιστικά</li>
                <li>• Αθλητικά & άλλα</li>
              </ul>
              <button
                onClick={() => router.push('/projects')}
                className="w-full px-6 py-3 bg-purple-700 text-white rounded-lg hover:bg-purple-600 transition font-semibold text-base"
              >
                Δες Έργα
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Πώς Λειτουργεί
            </h2>
            <p className="text-xl text-gray-600">
              Απλά βήματα για να αρχίσεις
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-900">1</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Εγγραφή</h3>
              <p className="text-gray-600 text-base">Δημιούργησε τον λογαριασμό σου γρήγορα και εύκολα</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-700">2</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Επιλογή</h3>
              <p className="text-gray-600 text-base">Διάλεξε την υπηρεσία που χρειάζεσαι ή θες να προσφέρεις</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-purple-700">3</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Σύνδεση</h3>
              <p className="text-gray-600 text-base">Συνδέσου με άλλους πολίτες και βοηθήστε ο ένας τον άλλον</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="text-3xl font-bold mb-4">🆘 HelpMeAnytime</div>
            <p className="text-gray-400 mb-8">Μαζί κάνουμε την Αθήνα καλύτερη</p>
            <div className="border-t border-gray-800 pt-8">
              <p className="text-gray-500">© 2025 HelpMeAnytime. Όλα τα δικαιώματα διατηρούνται.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
