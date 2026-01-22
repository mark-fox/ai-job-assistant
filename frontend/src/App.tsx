function App() {
  return (
    <div className="min-h-screen bg-slate-200 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-semibold tracking-tight text-slate-900">
              AI Job Assistant
            </span>
            <span className="text-xs uppercase text-slate-400">
              prototype
            </span>
          </div>
          <span className="text-xs text-slate-500">
            Backend: FastAPI • Frontend: React + Vite
          </span>
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 md:flex-row">
        <section className="flex-1 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Resume analysis
          </h2>
          <p className="mb-4 text-sm text-slate-700">
            Paste a resume to analyze it and store the result for later interview
            answers.
          </p>
          <textarea
            className="h-48 w-full resize-none rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            placeholder="Paste resume text here..."
          />
          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              className="rounded-xl border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-slate-400 hover:bg-slate-50"
            >
              Clear
            </button>
            <button
              type="button"
              className="rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500"
            >
              Analyze resume
            </button>
          </div>
        </section>

        <section className="flex-1 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Interview answer generation
          </h2>
          <p className="mb-4 text-sm text-slate-700">
            Provide a question, role, and company. The assistant will generate a
            tailored answer based on stored resume analyses.
          </p>

          <div className="mb-3 grid gap-3 md:grid-cols-2">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-700">
                Job title
              </label>
              <input
                type="text"
                className="rounded-xl border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                placeholder="Junior AI Engineer"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-700">
                Company name
              </label>
              <input
                type="text"
                className="rounded-xl border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                placeholder="Example Corp"
              />
            </div>
          </div>

          <div className="mb-3 flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-700">
              Interview question
            </label>
            <textarea
              className="h-24 w-full resize-none rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="Tell me about yourself."
            />
          </div>

          <div className="mt-3 flex justify-end">
            <button
              type="button"
              className="rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500"
            >
              Generate answer
            </button>
          </div>

          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Generated answer
            </p>
            <p className="text-sm text-slate-800">
              The generated interview answer will appear here.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
