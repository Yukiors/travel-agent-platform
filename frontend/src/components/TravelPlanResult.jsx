import React from 'react';
import './TravelPlanResult.css';

/**
 * 旅行计划结果展示组件
 */
const TravelPlanResult = ({ plan }) => {
  if (!plan || !plan.final_plan) {
    return null;
  }

  const { final_plan } = plan;

  return (
    <div className="travel-plan-result">
      <div className="plan-header">
        <h2>{plan.destination}之旅</h2>
        <p className="plan-summary">{final_plan.summary}</p>
      </div>

      {final_plan.highlights && final_plan.highlights.length > 0 && (
        <section className="plan-section">
          <h3>行程亮点</h3>
          <ul className="highlights-list">
            {final_plan.highlights.map((highlight, index) => (
              <li key={index}>{highlight}</li>
            ))}
          </ul>
        </section>
      )}

      {final_plan.itinerary && final_plan.itinerary.length > 0 && (
        <section className="plan-section">
          <h3>详细行程</h3>
          <div className="itinerary-list">
            {final_plan.itinerary.map((day, index) => (
              <div key={index} className="day-card">
                <div className="day-header">
                  <span className="day-number">第{day.day}天</span>
                  <span className="day-date">{day.date}</span>
                </div>
                <p className="day-description">{day.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {final_plan.budget_breakdown && (
        <section className="plan-section">
          <h3>预算分析</h3>
          <div className="budget-card">
            <div className="budget-total">
              <span className="budget-label">总费用</span>
              <span className="budget-amount">{final_plan.budget_breakdown.total_cost} 元/人</span>
            </div>
            <div className="budget-status">
              {final_plan.budget_breakdown.within_budget ? (
                <span className="badge badge-success">在预算内</span>
              ) : (
                <span className="badge badge-warning">超出预算</span>
              )}
            </div>
            <div className="budget-details">
              {Object.entries(final_plan.budget_breakdown.breakdown).map(([key, value]) => (
                <div key={key} className="budget-item">
                  <span className="budget-item-label">{key}</span>
                  <span className="budget-item-value">{value} 元</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {final_plan.tips && final_plan.tips.length > 0 && (
        <section className="plan-section">
          <h3>旅行建议</h3>
          <ul className="tips-list">
            {final_plan.tips.map((tip, index) => (
              <li key={index}>{tip}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
};

export default TravelPlanResult;
