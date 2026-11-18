import { useState } from 'react'
import { Button } from '@/components/base/buttons/button'
import { StatCards } from '@/components/application/dashboard/stat-cards'
import { DataTableExample } from '@/components/application/data-table/data-table'

export default function App() {
  const [dark, setDark] = useState(false)
  const toggle = () => {
    setDark((d) => {
      const next = !d
      document.documentElement.classList.toggle('dark', next)
      return next
    })
  }

  return (
    <div className="min-h-screen bg-background-full text-text-primary">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">BoardUI 组件包</h1>
            <p className="mt-1 text-sm text-text-secondary">
              React 19 + Tailwind CSS v4 · 经官方 CLI 安装（init + add）
            </p>
          </div>
          <Button variant="secondary" size="small" onClick={toggle}>
            {dark ? '切换浅色' : '切换深色'}
          </Button>
        </header>

        <StatCards variant="footer" columns={4} />

        <section className="flex flex-wrap items-center gap-3">
          <Button variant="primary">主要操作</Button>
          <Button variant="secondary">次要操作</Button>
          <Button variant="ghost">幽灵按钮</Button>
          <Button variant="danger">危险操作</Button>
        </section>

        <DataTableExample />
      </div>
    </div>
  )
}