import MonthlyView from "./pages/MonthlyView";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-primary text-white py-4 px-6 shadow-md">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-wide">MEU CONTROLE</h1>
          <span className="text-blue-200 text-xs font-medium tracking-wider uppercase">
            Financas Pessoais
          </span>
        </div>
      </header>
      <main>
        <MonthlyView />
      </main>
    </div>
  );
}
