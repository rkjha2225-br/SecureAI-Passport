
import { useState } from "react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Safely read API responses, including non-JSON error responses.
async function readApiResponse(response) {
  const text = await response.text();

  let data = {};

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text || "Invalid server response" };
  }

  if (!response.ok) {
    throw new Error(
      data.detail || `Request failed with status ${response.status}`
    );
  }

  return data;
}

function App() {
  const [activeTab, setActiveTab] = useState("Overview");

  const [message, setMessage] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [approverToken, setApproverToken] = useState("");

  const [notice, setNotice] = useState("");
  const [result, setResult] = useState(null);

  const [approvals, setApprovals] = useState([]);
  const [approvalMessage, setApprovalMessage] = useState("");

  const [auditLogs, setAuditLogs] = useState([]);
  const [auditMessage, setAuditMessage] = useState("");

  // Audit filters
  const [actionSearch, setActionSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [approverFilter, setApproverFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const recordsPerPage = 10;

  const [dashboardStats, setDashboardStats] = useState({
    total: "--",
    pending: "--",
    executed: "--",
    denied: "--",
  });

  const [statsMessage, setStatsMessage] = useState("");

  const menu = [
    "Overview",
    "AI Gateway",
    "Approvals",
    "Audit Logs",
  ];

  // Get records from API response
  function getRecords(data, keys) {
    if (Array.isArray(data)) {
      return data;
    }

    for (const key of keys) {
      if (Array.isArray(data[key])) {
        return data[key];
      }
    }

    return [];
  }

  // Common API headers
  function getApiHeaders() {
    return {
      "X-API-Key": apiKey.trim(),
    };
  }

  // Load approval requests
  async function loadApprovals() {
    if (!apiKey.trim()) {
      setApprovalMessage("Enter your API key first.");
      return;
    }

    setApprovalMessage("Loading approvals...");

    try {
      const response = await fetch(
        `${API_BASE_URL}/approvals`,
        {
          headers: getApiHeaders(),
        }
      );

      const data = await readApiResponse(response);

      const records = getRecords(data, ["approvals"]);

      setApprovals(records);

      setApprovalMessage(
        `${records.length} approval requests found.`
      );

    } catch (error) {
      setApprovalMessage(error.message);
    }
  }

  // Approve or reject a request
  async function decideApproval(approvalId, decision) {
    if (!apiKey.trim() || !approverToken.trim()) {
      setApprovalMessage(
        "Enter your API key and approver token."
      );
      return;
    }

    if (!["approve", "reject"].includes(decision)) {
      setApprovalMessage("Invalid approval action.");
      return;
    }

    try {
      setApprovalMessage("Processing approval...");

      const response = await fetch(
        `${API_BASE_URL}/approvals/${encodeURIComponent(
          approvalId
        )}/${decision}`,
        {
          method: "POST",
          headers: {
            "X-API-Key": apiKey.trim(),
            "X-Approver-Token": approverToken.trim(),
          },
        }
      );

      await readApiResponse(response);

      const status =
        decision === "approve" ? "approved" : "rejected";

      setApprovalMessage(
        `Request ${status} successfully.`
      );

      await loadApprovals();

    } catch (error) {
      setApprovalMessage(error.message);
    }
  }

  // Submit request to AI Gateway
  async function handleSubmit(event) {
    event.preventDefault();

    if (!apiKey.trim() || !message.trim()) {
      setNotice(
        "Enter both your API key and request."
      );
      return;
    }

    setNotice("Processing...");
    setResult(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/ai/execute`,
        {
          method: "POST",
          headers: {
            ...getApiHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_message: message.trim(),
          }),
        }
      );

      const data = await readApiResponse(response);

      setResult(data);
      setNotice("Request processed successfully.");
      setMessage("");

    } catch (error) {
      setNotice("Error: " + error.message);
    }
  }

  // Load audit logs
  async function loadAuditLogs() {
    if (!apiKey.trim()) {
      setAuditMessage("Enter your API key first.");
      return;
    }

    setAuditMessage("Loading audit logs...");

    try {
      const response = await fetch(
        `${API_BASE_URL}/audit`,
        {
          headers: getApiHeaders(),
        }
      );

      const data = await readApiResponse(response);

      const records = data.events || [];

      setAuditLogs(Array.isArray(records) ? records : []);
      setCurrentPage(1);

      setAuditMessage(
        `${records.length} audit records loaded.`
      );

    } catch (error) {
      setAuditMessage(error.message);
    }
  }

  // Load dashboard statistics
  async function loadDashboardStats() {
    if (!apiKey.trim()) {
      setStatsMessage("Enter your API key first.");
      return;
    }

    setStatsMessage("Loading dashboard statistics...");

    try {
      const headers = getApiHeaders();

      const [auditResponse, approvalResponse] =
        await Promise.all([
          fetch(`${API_BASE_URL}/audit`, { headers }),
          fetch(`${API_BASE_URL}/approvals`, { headers }),
        ]);

      const auditData = await readApiResponse(auditResponse);
      const approvalData = await readApiResponse(approvalResponse);

      const auditRecords = auditData.events || [];

      const approvalRecords = getRecords(
        approvalData,
        ["approvals"]
      );

      const executedCount = auditRecords.filter(
        (item) => item.status === "executed"
      ).length;

      const deniedCount = auditRecords.filter(
        (item) => item.status === "denied"
      ).length;

      const pendingCount = approvalRecords.filter(
        (item) => item.status === "pending"
      ).length;

      setDashboardStats({
        total: auditRecords.length,
        pending: pendingCount,
        executed: executedCount,
        denied: deniedCount,
      });

      setStatsMessage("Dashboard statistics updated.");

    } catch (error) {
      setStatsMessage("Error: " + error.message);
    }
  }

  // Filter audit logs in the frontend
  const filteredAuditLogs = auditLogs.filter((item) => {
    const matchesAction = String(item.action || "")
      .toLowerCase()
      .includes(actionSearch.toLowerCase());

    const matchesStatus =
      statusFilter === "all" ||
      String(item.status || "").toLowerCase() === statusFilter;

    const matchesApprover = String(item.approver_id || "")
      .toLowerCase()
      .includes(approverFilter.toLowerCase());

    return (
      matchesAction &&
      matchesStatus &&
      matchesApprover
    );
  });

  // Pagination calculations
  const totalPages = Math.ceil(
    filteredAuditLogs.length / recordsPerPage
  );

  const startIndex = (currentPage - 1) * recordsPerPage;

  const currentRecords = filteredAuditLogs.slice(
    startIndex,
    startIndex + recordsPerPage
  );

  function changeAuditFilter(setter, value) {
    setter(value);
    setCurrentPage(1);
  }

  return (
    <div className="app">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">S</div>

          <div>
            <h2>SecureAI</h2>
            <span>PASSPORT</span>
          </div>
        </div>

        <p className="menu-label">MAIN MENU</p>

        <nav>
          {menu.map((item) => (
            <button
              key={item}
              className={
                activeTab === item
                  ? "nav-item active"
                  : "nav-item"
              }
              onClick={() => setActiveTab(item)}
            >
              {item}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">

          <div className="security-status">
            <span className="status-dot"></span>

            <div>
              <strong>Gateway protected</strong>
              <small>Security layer active</small>
            </div>
          </div>

          <p className="version">
            SECUREAI PASSPORT · v1.0
          </p>

        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main">

        <header className="topbar">

          <div>
            <p className="breadcrumb">
              SECUREAI / WORKSPACE
            </p>

            <h1>{activeTab}</h1>
          </div>

          <span className="environment">
            DEVELOPMENT
          </span>

        </header>

        {/* OVERVIEW */}
        {activeTab === "Overview" && (
          <>

            <section className="welcome">

              <div>
                <p className="eyebrow">
                  SECURITY CONTROL CENTER
                </p>

                <h2>
                  AI actions. Under your control.
                </h2>

                <p>
                  Monitor requests, enforce policies, and
                  manage sensitive actions through one
                  secure gateway.
                </p>
              </div>

              <div className="shield">◇</div>

            </section>

            <section className="stats">

              {[
                {
                  title: "Total requests",
                  value: dashboardStats.total,
                },
                {
                  title: "Pending approvals",
                  value: dashboardStats.pending,
                },
                {
                  title: "Executed actions",
                  value: dashboardStats.executed,
                },
                {
                  title: "Denied actions",
                  value: dashboardStats.denied,
                },
              ].map((item) => (

                <div className="stat-card" key={item.title}>
                  <span>{item.title}</span>
                  <h3>{item.value}</h3>
                  <small>Live backend data</small>
                </div>

              ))}

            </section>

            <div className="stats-controls">

              <button
                className="refresh-button"
                onClick={loadDashboardStats}
              >
                Refresh Statistics ↻
              </button>

              {statsMessage && (
                <p className="notice">
                  {statsMessage}
                </p>
              )}

            </div>

            <section className="content-grid">

              <div className="panel command-panel">

                <div className="panel-heading">

                  <div>
                    <p className="eyebrow">
                      AI INTERFACE
                    </p>

                    <h3>Command Gateway</h3>
                  </div>

                  <span className="live-tag">READY</span>

                </div>

                <p className="panel-description">
                  Describe the action you want the AI to
                  interpret. The backend will validate it
                  before processing.
                </p>

                <form onSubmit={handleSubmit}>

                  <input
                    type="password"
                    value={apiKey}
                    onChange={(event) =>
                      setApiKey(event.target.value)
                    }
                    placeholder="Enter your SecureAI API key"
                    className="api-key-input"
                    autoComplete="off"
                  />

                  <textarea
                    value={message}
                    onChange={(event) =>
                      setMessage(event.target.value)
                    }
                    placeholder="Example: Show me all demo records..."
                  />

                  <div className="form-footer">

                    <span>Natural language input</span>

                    <button type="submit">
                      Submit request ↗
                    </button>

                  </div>

                </form>

                {notice && (
                  <p className="notice">{notice}</p>
                )}

                {result && (
                  <pre className="result-box">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                )}

                <div className="security-note">
                  AI suggestions do not bypass backend
                  security policies.
                </div>

              </div>

              <div className="panel approval-panel">

                <div className="panel-heading">

                  <div>
                    <p className="eyebrow">HUMAN CONTROL</p>
                    <h3>Approval Queue</h3>
                  </div>

                  <span className="count-tag">DEMO</span>

                </div>

                <div className="empty-state">
                  <div className="empty-icon">✓</div>
                  <h4>Approval management</h4>

                  <p>
                    Review sensitive action requests in
                    the approval section.
                  </p>
                </div>

                <button
                  className="text-button"
                  onClick={() => setActiveTab("Approvals")}
                >
                  Open approvals →
                </button>

              </div>

            </section>

            <section className="panel activity-panel">

              <div className="panel-heading">

                <div>
                  <p className="eyebrow">SYSTEM MONITOR</p>
                  <h3>Recent Activity</h3>
                </div>

                <button
                  className="text-button"
                  onClick={() => setActiveTab("Audit Logs")}
                >
                  View audit logs →
                </button>

              </div>

              <div className="empty-state compact">
                <p>
                  View recorded system events in Audit Logs.
                </p>
              </div>

            </section>

          </>
        )}

        {/* AI GATEWAY */}
        {activeTab === "AI Gateway" && (

          <section className="panel placeholder-panel">

            <p className="eyebrow">AI INTERFACE</p>
            <h2>AI Gateway</h2>

            <p>
              Submit natural-language requests from the
              Overview page.
            </p>

            <button
              onClick={() => setActiveTab("Overview")}
            >
              Back to Overview
            </button>

          </section>

        )}

        {/* APPROVAL MANAGEMENT */}
        {activeTab === "Approvals" && (

          <section className="panel approval-management">

            <div className="panel-heading">

              <div>
                <p className="eyebrow">HUMAN CONTROL</p>
                <h3>Approval Management</h3>
              </div>

              <button
                className="refresh-button"
                onClick={loadApprovals}
              >
                Refresh
              </button>

            </div>

            <div className="approval-inputs">

              <input
                type="password"
                value={apiKey}
                onChange={(event) =>
                  setApiKey(event.target.value)
                }
                placeholder="Enter API key"
                autoComplete="off"
              />

              <input
                type="password"
                value={approverToken}
                onChange={(event) =>
                  setApproverToken(event.target.value)
                }
                placeholder="Enter Approver Token"
                autoComplete="off"
              />

            </div>

            {approvalMessage && (
              <p className="notice">{approvalMessage}</p>
            )}

            <div className="approval-list">

              {approvals.length === 0 ? (

                <p className="empty-message">
                  No requests loaded. Click Refresh.
                </p>

              ) : (

                approvals.map((item) => (

                  <div
                    className="approval-item"
                    key={item.approval_id}
                  >

                    <div>
                      <h4>{item.action}</h4>

                      <p>ID: {item.approval_id}</p>

                      <span
                        className={`approval-status ${item.status}`}
                      >
                        {item.status}
                      </span>
                    </div>

                    {item.status === "pending" && (

                      <div className="approval-actions">

                        <button
                          className="approve-button"
                          onClick={() =>
                            decideApproval(
                              item.approval_id,
                              "approve"
                            )
                          }
                        >
                          Approve
                        </button>

                        <button
                          className="reject-button"
                          onClick={() =>
                            decideApproval(
                              item.approval_id,
                              "reject"
                            )
                          }
                        >
                          Reject
                        </button>

                      </div>

                    )}

                  </div>

                ))

              )}

            </div>

          </section>

        )}

        {/* AUDIT LOGS */}
        {activeTab === "Audit Logs" && (

          <section className="panel audit-management">

            <div className="panel-heading">

              <div>
                <p className="eyebrow">SYSTEM MONITOR</p>
                <h3>Audit Logs</h3>
              </div>

              <button
                className="refresh-button"
                onClick={loadAuditLogs}
              >
                Refresh
              </button>

            </div>

            <p className="panel-description">
              Review recorded actions and security events
              from your backend.
            </p>

            {auditMessage && (
              <p className="notice">{auditMessage}</p>
            )}

            {/* FILTERS */}
            <div className="audit-filters">

              <input
                type="text"
                placeholder="Search action..."
                value={actionSearch}
                onChange={(event) =>
                  changeAuditFilter(
                    setActionSearch,
                    event.target.value
                  )
                }
              />

              <select
                value={statusFilter}
                onChange={(event) =>
                  changeAuditFilter(
                    setStatusFilter,
                    event.target.value
                  )
                }
              >
                <option value="all">All statuses</option>
                <option value="executed">Executed</option>
                <option value="denied">Denied</option>
                <option value="approval_required">
                  Approval Required
                </option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>

              <input
                type="text"
                placeholder="Search approver ID..."
                value={approverFilter}
                onChange={(event) =>
                  changeAuditFilter(
                    setApproverFilter,
                    event.target.value
                  )
                }
              />

            </div>

            <p className="audit-count">
              Showing {currentRecords.length} of{" "}
              {filteredAuditLogs.length} matching records
            </p>

            {/* AUDIT RECORDS */}
            <div className="audit-list">

              {currentRecords.length === 0 ? (

                <p className="empty-message">
                  No matching audit records found.
                </p>

              ) : (

                currentRecords.map((item, index) => (

                  <div
                    className="audit-item"
                    key={item.timestamp || index}
                  >

                    <div className="audit-header">

                      <h4>
                        {item.action || "Unknown action"}
                      </h4>

                      <span
                        className={`approval-status ${item.status || ""}`}
                      >
                        {item.status || "Unknown"}
                      </span>

                    </div>

                    <p>
                      <strong>Timestamp:</strong>{" "}
                      {item.timestamp || "Not available"}
                    </p>

                    <p>
                      <strong>Reason:</strong>{" "}
                      {item.reason || "Not available"}
                    </p>

                    <p>
                      <strong>Approver ID:</strong>{" "}
                      {item.approver_id || "Not available"}
                    </p>

                  </div>

                ))

              )}

            </div>

            {/* PAGINATION */}
            {filteredAuditLogs.length > 0 && (

              <div className="pagination">

                <button
                  disabled={currentPage === 1}
                  onClick={() =>
                    setCurrentPage(currentPage - 1)
                  }
                >
                  Previous
                </button>

                <span>
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  disabled={currentPage >= totalPages}
                  onClick={() =>
                    setCurrentPage(currentPage + 1)
                  }
                >
                  Next
                </button>

              </div>

            )}

          </section>

        )}

        <footer>
          SecureAI Passport · AI security gateway · Development preview
        </footer>

      </main>

    </div>
  );
}

export default App;
