import { useEffect, useState } from "react";
import { API_BASE_URL } from "./config";

type StatusResponse = {
  status: string;
  version: string;
  environment: string;
  llm_provider: string;
  checks: {
    database: string;
  };
};

type ResumeAnalysis = {
  id: number;
  user_id: number | null;
  resume_text: string;
  summary: string;
  created_at: string;
  provider: string;
};

type InterviewAnswer = {
  id: number;
  user_id: number | null;
  resume_analysis_id: number | null;
  question: string;
  job_title: string | null;
  company_name: string | null;
  answer: string;
  created_at: string;
  provider: string;
};

function App() {
  const [appStatus, setAppStatus] = useState<StatusResponse | null>(null);
  const [appStatusError, setAppStatusError] = useState<string | null>(null);

  const [resumeText, setResumeText] = useState("");
  const [resumeSummary, setResumeSummary] = useState<string | null>(null);
  const [resumeProvider, setResumeProvider] = useState<string | null>(null);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeError, setResumeError] = useState<string | null>(null);

  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [question, setQuestion] = useState("");
  const [generatedAnswer, setGeneratedAnswer] = useState<string | null>(null);
  const [answerProvider, setAnswerProvider] = useState<string | null>(null);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [answerError, setAnswerError] = useState<string | null>(null);

  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [analysisAnswers, setAnalysisAnswers] = useState<InterviewAnswer[]>([]);

  const [resumeAnalysisId, setResumeAnalysisId] = useState<number | null>(null);
  const [resumeAnswers, setResumeAnswers] = useState<
    { id: number; question: string; answer: string; provider: string; created_at: string | null }[]
  >([]);
  const [generatedAnswerCreatedAt, setGeneratedAnswerCreatedAt] = useState<string | null>(null);

  const [deleteResumeLoading, setDeleteResumeLoading] = useState(false);
  const [deleteAnswerLoading, setDeleteAnswerLoading] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/status`);
        if (!response.ok) {
          setAppStatusError("Unable to fetch backend status.");
          return;
        }
        const data = (await response.json()) as StatusResponse;
        setAppStatus(data);
      } catch {
        setAppStatusError("Unable to reach backend.");
      }
    };

    fetchStatus();
  }, []);

  const handleClearResume = () => {
    setResumeText("");
    setResumeSummary(null);
    setResumeProvider(null);
    setResumeError(null);
    setResumeAnalysisId(null);
    setResumeAnswers([]);
  };

  const handleAnalyzeResume = async () => {
    setResumeError(null);
    setResumeSummary(null);
    setResumeProvider(null);
    setResumeAnalysisId(null);
    setResumeAnswers([]);

    if (!resumeText.trim()) {
      setResumeError("Resume text is required.");
      return;
    }

    setResumeLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: null,
          resume_text: resumeText,
        }),
      });

      if (!response.ok) {
        if (response.status === 422) {
          setResumeError("Resume text must be at least 20 characters.");
        } else if (response.status === 404) {
          setResumeError("User not found for this request.");
        } else {
          setResumeError("Failed to analyze resume. Please try again.");
        }
        return;
      }

      const data = await response.json();
      setResumeSummary(data.summary ?? "No summary returned.");
      setResumeProvider(data.provider ?? null);

      if (typeof data.id === "number") {
        setResumeAnalysisId(data.id);
        await fetchAnswersForResume(data.id);
      }
    } catch (error) {
      setResumeError("Network error while analyzing resume.");
    } finally {
      setResumeLoading(false);
    }
  };

  const handleGenerateAnswer = async () => {
    setAnswerError(null);
    setGeneratedAnswer(null);
    setAnswerProvider(null);
    setGeneratedAnswerCreatedAt(null);

    if (!question.trim()) {
      setAnswerError("Interview question is required.");
      return;
    }

    setAnswerLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate/answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: null,
          resume_analysis_id: resumeAnalysisId,
          question,
          job_title: jobTitle || null,
          company_name: companyName || null,
        }),
      });

      if (!response.ok) {
        if (response.status === 422) {
          setAnswerError("Question must be at least 5 characters.");
        } else if (response.status === 404) {
          setAnswerError("Related user or resume analysis was not found.");
        } else {
          setAnswerError("Failed to generate answer. Please try again.");
        }
        return;
      }

      const data = await response.json();
      setGeneratedAnswer(data.answer ?? "No answer returned.");
      setAnswerProvider(data.provider ?? null);
      setGeneratedAnswerCreatedAt(data.created_at ?? null);

      const analysisIdFromResponse =
        typeof data.resume_analysis_id === "number"
          ? data.resume_analysis_id
          : resumeAnalysisId;

      if (analysisIdFromResponse != null) {
        setResumeAnalysisId(analysisIdFromResponse);
        await fetchAnswersForResume(analysisIdFromResponse);
      }
    } catch (error) {
      setAnswerError("Network error while generating answer.");
    } finally {
      setAnswerLoading(false);
    }
  };

  const fetchAnswersForResume = async (analysisId: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/resume/${analysisId}/answers?limit=10&offset=0`,
      );

      if (!response.ok) {
        console.error("Failed to fetch answers for resume", await response.text());
        return;
      }

      const data = await response.json();
      setResumeAnswers(
        (data ?? []).map((item: any) => ({
          id: item.id,
          question: item.question,
          answer: item.answer,
          provider: item.provider,
          created_at: item.created_at ?? null,
        })),
      );
    } catch (error) {
      console.error("Network error while fetching answers for resume", error);
    }
  };

  const handleSelectResumeAnswer = (answer: {
    id: number;
    question: string;
    answer: string;
    provider: string;
  }) => {
    setGeneratedAnswer(answer.answer);
    setAnswerProvider(answer.provider);
    setQuestion(answer.question);
  };

  const handleDeleteResumeAnalysis = async () => {
    if (resumeAnalysisId == null) {
      return;
    }

    setResumeError(null);
    setDeleteResumeLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/${resumeAnalysisId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        if (response.status === 404) {
          setResumeError("Resume analysis was not found.");
        } else if (response.status === 403) {
          setResumeError("You do not have permission to delete this resume analysis.");
        } else if (response.status === 401) {
          setResumeError("Authentication is required to delete this resume analysis.");
        } else {
          setResumeError("Failed to delete resume analysis. Please try again.");
        }
        return;
      }

      // Clear analysis-related state on successful delete
      setResumeAnalysisId(null);
      setResumeSummary(null);
      setResumeProvider(null);
      setResumeAnswers([]);
    } catch (error) {
      setResumeError("Network error while deleting resume analysis.");
    } finally {
      setDeleteResumeLoading(false);
    }
  };

  const handleDeleteAnswer = async (answerId: number) => {
    setAnswerError(null);
    setDeleteAnswerLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/answers/${answerId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        if (response.status === 404) {
          setAnswerError("This answer was not found.");
        } else if (response.status === 403) {
          setAnswerError("You do not have permission to delete this answer.");
        } else if (response.status === 401) {
          setAnswerError("Authentication is required to delete answers.");
        } else {
          setAnswerError("Failed to delete answer. Please try again.");
        }
        return;
      }

      setResumeAnswers((prev) => prev.filter((a) => a.id !== answerId));
    } catch (error) {
      setAnswerError("Network error while deleting answer.");
    } finally {
      setDeleteAnswerLoading(false);
    }
  };

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
          <div className="flex flex-col items-end gap-1">
            {appStatus && (
              <span className="text-xs text-slate-500">
                Env: {appStatus.environment} • Provider: {appStatus.llm_provider} •
                DB: {appStatus.checks?.database ?? "unknown"}
              </span>
            )}
            {appStatusError && (
              <span className="text-xs text-red-600">
                {appStatusError}
              </span>
            )}
            {!appStatus && !appStatusError && (
              <span className="text-xs text-slate-400">
                Checking backend status…
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 md:flex-row">
        <section className="flex-1 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Resume analysis
          </h2>
          <p className="mb-4 text-sm text-slate-700">
            Paste a resume to analyze it and store the result for later
            interview answers.
          </p>
          <textarea
            className="h-48 w-full resize-none rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            placeholder="Paste resume text here..."
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
          />
          {resumeError && (
            <p className="mt-2 text-xs text-red-600">{resumeError}</p>
          )}
          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              className="rounded-xl border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-slate-400 hover:bg-slate-50"
              onClick={handleClearResume}
              disabled={resumeLoading || deleteResumeLoading}
            >
              Clear
            </button>
            <button
              type="button"
              className="rounded-xl border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 hover:border-red-300 hover:bg-red-100 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50 disabled:text-red-300"
              onClick={handleDeleteResumeAnalysis}
              disabled={deleteResumeLoading || resumeAnalysisId == null}
            >
              {deleteResumeLoading ? "Deleting..." : "Delete analysis"}
            </button>
            <button
              type="button"
              className="rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
              onClick={handleAnalyzeResume}
              disabled={resumeLoading}
            >
              {resumeLoading ? "Analyzing..." : "Analyze resume"}
            </button>
          </div>
          {resumeSummary && (
            <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Analysis summary
              </p>
              <p className="text-sm text-slate-800">{resumeSummary}</p>
              {resumeProvider && (
                <p className="mt-1 text-xs text-slate-500">
                  Provider: {resumeProvider}
                </p>
              )}
            </div>
          )}
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
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
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
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
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
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>

          {answerError && (
            <p className="mt-2 text-xs text-red-600">{answerError}</p>
          )}

          <div className="mt-3 flex justify-end">
            <button
              type="button"
              className="rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
              onClick={handleGenerateAnswer}
              disabled={answerLoading}
            >
              {answerLoading ? "Generating..." : "Generate answer"}
            </button>
          </div>

          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Generated answer
            </p>
            <p className="text-sm text-slate-800">
              {generatedAnswer ?? "The generated interview answer will appear here."}
            </p>
            {(answerProvider || generatedAnswerCreatedAt) && (
              <p className="mt-1 text-xs text-slate-500">
                {answerProvider && <>Provider: {answerProvider}</>}
                {answerProvider && generatedAnswerCreatedAt && " • "}
                {generatedAnswerCreatedAt && (
                  <>Created: {new Date(generatedAnswerCreatedAt).toLocaleString()}</>
                )}
              </p>
            )}
          </div>

          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Answers for this resume
            </p>

            {resumeAnalysisId == null && (
              <p className="text-sm text-slate-500">
                Analyze a resume first to see related answers.
              </p>
            )}

            {resumeAnalysisId != null && resumeAnswers.length === 0 && (
              <p className="text-sm text-slate-500">
                No answers have been generated for this resume yet.
              </p>
            )}

            {resumeAnalysisId != null && resumeAnswers.length > 0 && (
              <div className="mt-2 max-h-48 space-y-2 overflow-y-auto">
                {resumeAnswers.map((answer) => (
                  <div
                    key={answer.id}
                    className="w-full cursor-pointer rounded-lg border border-slate-200 bg-white p-2 text-left shadow-sm transition hover:border-blue-400 hover:bg-blue-50"
                    onClick={() => handleSelectResumeAnswer(answer)}
                  >
                    <p className="text-xs font-semibold text-slate-700">
                      Q: {answer.question}
                    </p>
                    <p className="mt-1 text-xs text-slate-800 line-clamp-3">
                      {answer.answer}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Provider: {answer.provider}
                      {answer.created_at && (
                        <> • Created: {new Date(answer.created_at).toLocaleString()}</>
                      )}
                    </p>
                    <div className="mt-2 flex justify-end">
                      <button
                        type="button"
                        className="rounded-lg border border-red-200 bg-red-50 px-2 py-0.5 text-[11px] font-medium text-red-700 hover:border-red-300 hover:bg-red-100 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50 disabled:text-red-300"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteAnswer(answer.id);
                        }}
                        disabled={deleteAnswerLoading}
                      >
                        {deleteAnswerLoading ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;