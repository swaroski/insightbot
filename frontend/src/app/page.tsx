'use client'

import { useState } from 'react'
import { Search, Upload, BarChart3, FileText, Brain, Sparkles } from 'lucide-react'
import { QueryInterface } from '@/components/QueryInterface'
import { UploadInterface } from '@/components/UploadInterface'
import { AnalyticsInterface } from '@/components/AnalyticsInterface'
import { HistoryInterface } from '@/components/HistoryInterface'

type TabType = 'query' | 'upload' | 'analytics' | 'history'

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('query')

  const tabs = [
    { id: 'query', label: 'Query', icon: Search, component: QueryInterface },
    { id: 'upload', label: 'Upload', icon: Upload, component: UploadInterface },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, component: AnalyticsInterface },
    { id: 'history', label: 'History', icon: FileText, component: HistoryInterface },
  ] as const

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || QueryInterface

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">InsightBot</h1>
                <p className="text-xs text-slate-500">AI-Powered Knowledge Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-slate-600">Powered by GPT-4o</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-fade-in">
          <ActiveComponent />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-sm text-slate-500">
            <p>© 2024 InsightBot. Built with Next.js, FastAPI, and LangGraph.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}