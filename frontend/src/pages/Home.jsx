import React, { useState } from 'react';
import TravelPlanForm from '../components/TravelPlanForm';
import TravelPlanResult from '../components/TravelPlanResult';
import { createTravelPlan } from '../services/api';
import './Home.css';

/**
 * 主页面组件
 */
const Home = () => {
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (preferences) => {
    setLoading(true);
    setError(null);
    setPlan(null);

    try {
      const result = await createTravelPlan(preferences);
      setPlan(result);
    } catch (err) {
      setError('规划失败，请稍后重试');
      console.error('Error creating travel plan:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPlan(null);
    setError(null);
  };

  return (
    <div className="home-page">
      <header className="page-header">
        <div className="container">
          <h1>AI 旅行规划助手</h1>
          <p className="subtitle">智能定制您的完美旅程</p>
        </div>
      </header>

      <main className="page-main">
        <div className="container">
          {!plan ? (
            <div className="card form-card">
              <h2>开始规划您的旅程</h2>
              <TravelPlanForm onSubmit={handleSubmit} loading={loading} />
              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}
            </div>
          ) : (
            <div className="result-container">
              <div className="result-actions">
                <button className="btn-secondary" onClick={handleReset}>
                  重新规划
                </button>
              </div>
              <div className="card result-card">
                <TravelPlanResult plan={plan} />
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="page-footer">
        <div className="container">
          <p>&copy; 2026 AI 旅行规划助手. Powered by LangGraph & Claude.</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
