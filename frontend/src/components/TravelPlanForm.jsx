import React, { useState } from 'react';
import './TravelPlanForm.css';

/**
 * 旅行规划表单组件
 */
const TravelPlanForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    destination: '',
    start_date: '',
    end_date: '',
    budget: '',
    interests: [],
    num_travelers: 1,
  });

  const interestOptions = [
    '历史文化', '美食', '自然风光', '购物', '户外运动',
    '艺术', '摄影', '夜生活', '亲子', '休闲放松'
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleInterestToggle = (interest) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const preferences = {
      ...formData,
      budget: formData.budget ? parseFloat(formData.budget) : null,
      num_travelers: parseInt(formData.num_travelers),
    };
    onSubmit(preferences);
  };

  const isValid = formData.destination && formData.start_date && formData.end_date;

  return (
    <form className="travel-plan-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="destination">目的地 *</label>
        <input
          type="text"
          id="destination"
          name="destination"
          value={formData.destination}
          onChange={handleChange}
          placeholder="例如：杭州、北京、上海"
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="start_date">出发日期 *</label>
          <input
            type="date"
            id="start_date"
            name="start_date"
            value={formData.start_date}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="end_date">返程日期 *</label>
          <input
            type="date"
            id="end_date"
            name="end_date"
            value={formData.end_date}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="budget">预算（元/人）</label>
          <input
            type="number"
            id="budget"
            name="budget"
            value={formData.budget}
            onChange={handleChange}
            placeholder="例如：5000"
            min="0"
          />
        </div>

        <div className="form-group">
          <label htmlFor="num_travelers">人数</label>
          <input
            type="number"
            id="num_travelers"
            name="num_travelers"
            value={formData.num_travelers}
            onChange={handleChange}
            min="1"
            max="20"
          />
        </div>
      </div>

      <div className="form-group">
        <label>旅行偏好（可多选）</label>
        <div className="interest-chips">
          {interestOptions.map(interest => (
            <button
              key={interest}
              type="button"
              className={`chip ${formData.interests.includes(interest) ? 'active' : ''}`}
              onClick={() => handleInterestToggle(interest)}
            >
              {interest}
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="btn-primary submit-btn"
        disabled={!isValid || loading}
      >
        {loading ? (
          <>
            <span className="loading"></span>
            <span style={{ marginLeft: '0.5rem' }}>规划中...</span>
          </>
        ) : (
          '开始规划'
        )}
      </button>
    </form>
  );
};

export default TravelPlanForm;
