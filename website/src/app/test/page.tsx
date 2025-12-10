// Test page για το usePledges hook
'use client'

import { usePledges } from '@/hooks/usePledges'
import { useState } from 'react'

export default function TestPledgePage() {
  const { pledges, stats, loading, error, createPledge } = usePledges('1')
  const [pledgeType, setPledgeType] = useState<'money' | 'time' | 'materials'>('money')
  const [amount, setAmount] = useState(50)
  const [hours, setHours] = useState(5)
  const [materials, setMaterials] = useState('Paint and brushes')

  const handleCreatePledge = async () => {
    try {
      const pledgeData: any = {
        project_id: '1',
        type: pledgeType,
        description: `Test ${pledgeType} pledge`
      }

      if (pledgeType === 'money') pledgeData.amount = amount
      if (pledgeType === 'time') pledgeData.hours = hours
      if (pledgeType === 'materials') pledgeData.materials = materials

      await createPledge(pledgeData)
      alert('✅ Pledge created successfully!')
    } catch (err) {
      alert('❌ Failed to create pledge')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">🧪 Test Pledges API</h1>

        {loading && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
            Loading...
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            Error: {error}
          </div>
        )}

        {/* Stats Display */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4">📊 Real-time Stats</h2>
          
          {stats ? (
            <>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    €{stats.total_money}
                  </div>
                  <div className="text-sm text-gray-600">Money</div>
                  <div className="text-xs text-gray-500">
                    {stats.breakdown.money_pledges} pledges
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {stats.total_hours}h
                  </div>
                  <div className="text-sm text-gray-600">Hours</div>
                  <div className="text-xs text-gray-500">
                    {stats.breakdown.time_pledges} pledges
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">
                    {stats.total_materials}
                  </div>
                  <div className="text-sm text-gray-600">Materials</div>
                  <div className="text-xs text-gray-500">
                    {stats.breakdown.materials_pledges} pledges
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-semibold">Progress</span>
                  <span className="font-bold text-blue-600">
                    {stats.progress_percentage}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-green-400 to-blue-500 h-6 rounded-full transition-all duration-1000 ease-out flex items-center justify-center text-white text-xs font-bold"
                    style={{ width: `${stats.progress_percentage}%` }}
                  >
                    {stats.progress_percentage > 10 && `${stats.progress_percentage}%`}
                  </div>
                </div>
              </div>

              <div className="text-center text-sm text-gray-600">
                🙌 {stats.pledge_count} people supporting this project
              </div>
            </>
          ) : (
            <p className="text-gray-500">No stats available</p>
          )}
        </div>

        {/* Create Pledge Form */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4">🎯 Create Test Pledge</h2>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              Pledge Type
            </label>
            <select
              value={pledgeType}
              onChange={(e) => setPledgeType(e.target.value as any)}
              className="w-full p-2 border rounded"
            >
              <option value="money">💰 Money</option>
              <option value="time">⏰ Time</option>
              <option value="materials">🛠️ Materials</option>
            </select>
          </div>

          {pledgeType === 'money' && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Amount (€)
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full p-2 border rounded"
              />
            </div>
          )}

          {pledgeType === 'time' && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Hours
              </label>
              <input
                type="number"
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
                className="w-full p-2 border rounded"
              />
            </div>
          )}

          {pledgeType === 'materials' && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Materials Description
              </label>
              <input
                type="text"
                value={materials}
                onChange={(e) => setMaterials(e.target.value)}
                className="w-full p-2 border rounded"
              />
            </div>
          )}

          <button
            onClick={handleCreatePledge}
            disabled={loading}
            className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Pledge'}
          </button>
        </div>

        {/* Pledges List */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-4">📋 All Pledges</h2>
          
          {pledges.length > 0 ? (
            <div className="space-y-2">
              {pledges.map((pledge) => (
                <div
                  key={pledge.id}
                  className="border-l-4 border-blue-500 bg-blue-50 p-3 rounded"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-semibold">
                        {pledge.type === 'money' && `💰 €${pledge.amount}`}
                        {pledge.type === 'time' && `⏰ ${pledge.hours}h`}
                        {pledge.type === 'materials' && `🛠️ ${pledge.materials}`}
                      </span>
                      <p className="text-sm text-gray-600 mt-1">
                        {pledge.description}
                      </p>
                    </div>
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                      {pledge.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">
              No pledges yet. Create one above!
            </p>
          )}
        </div>

        {/* Debug Info */}
        <div className="mt-8 bg-gray-800 text-white rounded-lg p-4">
          <h3 className="font-bold mb-2">🐛 Debug Info</h3>
          <pre className="text-xs overflow-auto">
            {JSON.stringify({ pledges, stats, loading, error }, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}
