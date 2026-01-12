import { useState } from 'react';
import { submitOptimization } from '../api/client';

function UploadForm({ onOptimizationStart }) {
  const [formData, setFormData] = useState({
    pvCapexPerMw: '',
    bessCapexPerMwh: '',
    discountRate: '',
    interconnectionCapacityMw: '',
    onsiteLoadPricePerMwh: '',
    onsiteLoadMaxMw: '',
    yoyPriceEscalationRate: '',
    pvMaxSizeMw: '',
    bessMaxSizeMwh: '',
  });

  const [files, setFiles] = useState({
    pvProduction: null,
    pricing: null,
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleFileChange = (e) => {
    const { name, files: fileList } = e.target;
    if (fileList && fileList.length > 0) {
      setFiles((prev) => ({
        ...prev,
        [name]: fileList[0],
      }));
      // Clear error for this field
      if (errors[name]) {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors[name];
          return newErrors;
        });
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validate required files
    if (!files.pvProduction) {
      newErrors.pvProduction = 'PV production CSV file is required';
    }
    if (!files.pricing) {
      newErrors.pricing = 'Pricing CSV file is required';
    }

    // Validate required numeric fields
    const requiredFields = [
      'pvCapexPerMw',
      'bessCapexPerMwh',
      'discountRate',
      'interconnectionCapacityMw',
      'onsiteLoadPricePerMwh',
      'onsiteLoadMaxMw',
      'yoyPriceEscalationRate',
    ];

    requiredFields.forEach((field) => {
      const value = formData[field];
      if (!value || value.trim() === '') {
        newErrors[field] = 'This field is required';
      } else if (isNaN(parseFloat(value)) || parseFloat(value) <= 0) {
        newErrors[field] = 'Must be a positive number';
      }
    });

    // Validate discount rate (0-1)
    if (formData.discountRate) {
      const rate = parseFloat(formData.discountRate);
      if (rate < 0 || rate > 1) {
        newErrors.discountRate = 'Discount rate must be between 0 and 1 (e.g., 0.08 for 8%)';
      }
    }

    // Validate optional fields if provided
    if (formData.pvMaxSizeMw && (isNaN(parseFloat(formData.pvMaxSizeMw)) || parseFloat(formData.pvMaxSizeMw) <= 0)) {
      newErrors.pvMaxSizeMw = 'Must be a positive number';
    }
    if (formData.bessMaxSizeMwh && (isNaN(parseFloat(formData.bessMaxSizeMwh)) || parseFloat(formData.bessMaxSizeMwh) <= 0)) {
      newErrors.bessMaxSizeMwh = 'Must be a positive number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Create FormData for multipart/form-data request
      const submitData = new FormData();

      // Add files
      submitData.append('pv_production_file', files.pvProduction);
      submitData.append('pricing_file', files.pricing);

      // Add numeric parameters
      submitData.append('pv_capex_per_mw', formData.pvCapexPerMw);
      submitData.append('bess_capex_per_mwh', formData.bessCapexPerMwh);
      submitData.append('discount_rate', formData.discountRate);
      submitData.append('interconnection_capacity_mw', formData.interconnectionCapacityMw);
      submitData.append('onsite_load_price_per_mwh', formData.onsiteLoadPricePerMwh);
      submitData.append('onsite_load_max_mw', formData.onsiteLoadMaxMw);
      submitData.append('yoy_price_escalation_rate', formData.yoyPriceEscalationRate);

      // Add optional parameters if provided
      if (formData.pvMaxSizeMw) {
        submitData.append('pv_max_size_mw', formData.pvMaxSizeMw);
      }
      if (formData.bessMaxSizeMwh) {
        submitData.append('bess_max_size_mwh', formData.bessMaxSizeMwh);
      }

      const taskId = await submitOptimization(submitData);
      onOptimizationStart(taskId);
    } catch (error) {
      console.error('Error submitting optimization:', error);
      setErrors({
        submit: error.response?.data?.detail || 'Failed to submit optimization. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="upload-form">
      <h2>Solar + Storage Optimization</h2>
      <p className="subtitle">Upload CSV files and enter parameters to optimize your solar + storage configuration</p>

      <form onSubmit={handleSubmit}>
        {/* File Uploads */}
        <div className="form-section">
          <h3>Data Files</h3>
          
          <div className="form-group">
            <label htmlFor="pvProduction">
              PV Production Profile (CSV) <span className="required">*</span>
            </label>
            <input
              type="file"
              id="pvProduction"
              name="pvProduction"
              accept=".csv"
              onChange={handleFileChange}
              className={errors.pvProduction ? 'error' : ''}
            />
            {errors.pvProduction && <span className="error-message">{errors.pvProduction}</span>}
            <small>Expected format: Hour,Production_MWh_per_MW (8760 hours)</small>
          </div>

          <div className="form-group">
            <label htmlFor="pricing">
              Nodal Pricing Data (CSV) <span className="required">*</span>
            </label>
            <input
              type="file"
              id="pricing"
              name="pricing"
              accept=".csv"
              onChange={handleFileChange}
              className={errors.pricing ? 'error' : ''}
            />
            {errors.pricing && <span className="error-message">{errors.pricing}</span>}
            <small>Expected format: Hour,Price_per_MWh (8760 hours)</small>
          </div>
        </div>

        {/* Financial Parameters */}
        <div className="form-section">
          <h3>Financial Parameters</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="pvCapexPerMw">
                PV CAPEX ($/MW) <span className="required">*</span>
              </label>
              <input
                type="number"
                id="pvCapexPerMw"
                name="pvCapexPerMw"
                value={formData.pvCapexPerMw}
                onChange={handleInputChange}
                step="1000"
                min="0"
                className={errors.pvCapexPerMw ? 'error' : ''}
              />
              {errors.pvCapexPerMw && <span className="error-message">{errors.pvCapexPerMw}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="bessCapexPerMwh">
                BESS CAPEX ($/MWh) <span className="required">*</span>
              </label>
              <input
                type="number"
                id="bessCapexPerMwh"
                name="bessCapexPerMwh"
                value={formData.bessCapexPerMwh}
                onChange={handleInputChange}
                step="1000"
                min="0"
                className={errors.bessCapexPerMwh ? 'error' : ''}
              />
              {errors.bessCapexPerMwh && <span className="error-message">{errors.bessCapexPerMwh}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="discountRate">
                Discount Rate <span className="required">*</span>
              </label>
              <input
                type="number"
                id="discountRate"
                name="discountRate"
                value={formData.discountRate}
                onChange={handleInputChange}
                step="0.01"
                min="0"
                max="1"
                className={errors.discountRate ? 'error' : ''}
              />
              {errors.discountRate && <span className="error-message">{errors.discountRate}</span>}
              <small>Enter as decimal (e.g., 0.08 for 8%)</small>
            </div>

            <div className="form-group">
              <label htmlFor="yoyPriceEscalationRate">
                Price Escalation Rate <span className="required">*</span>
              </label>
              <input
                type="number"
                id="yoyPriceEscalationRate"
                name="yoyPriceEscalationRate"
                value={formData.yoyPriceEscalationRate}
                onChange={handleInputChange}
                step="0.01"
                min="0"
                max="1"
                className={errors.yoyPriceEscalationRate ? 'error' : ''}
              />
              {errors.yoyPriceEscalationRate && <span className="error-message">{errors.yoyPriceEscalationRate}</span>}
              <small>Enter as decimal (e.g., 0.02 for 2%)</small>
            </div>
          </div>
        </div>

        {/* System Constraints */}
        <div className="form-section">
          <h3>System Constraints</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="interconnectionCapacityMw">
                Interconnection Capacity (MW) <span className="required">*</span>
              </label>
              <input
                type="number"
                id="interconnectionCapacityMw"
                name="interconnectionCapacityMw"
                value={formData.interconnectionCapacityMw}
                onChange={handleInputChange}
                step="1"
                min="0"
                className={errors.interconnectionCapacityMw ? 'error' : ''}
              />
              {errors.interconnectionCapacityMw && <span className="error-message">{errors.interconnectionCapacityMw}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="onsiteLoadMaxMw">
                On-site Load Max (MW) <span className="required">*</span>
              </label>
              <input
                type="number"
                id="onsiteLoadMaxMw"
                name="onsiteLoadMaxMw"
                value={formData.onsiteLoadMaxMw}
                onChange={handleInputChange}
                step="1"
                min="0"
                className={errors.onsiteLoadMaxMw ? 'error' : ''}
              />
              {errors.onsiteLoadMaxMw && <span className="error-message">{errors.onsiteLoadMaxMw}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="onsiteLoadPricePerMwh">
                On-site Load Price ($/MWh) <span className="required">*</span>
              </label>
              <input
                type="number"
                id="onsiteLoadPricePerMwh"
                name="onsiteLoadPricePerMwh"
                value={formData.onsiteLoadPricePerMwh}
                onChange={handleInputChange}
                step="0.01"
                min="0"
                className={errors.onsiteLoadPricePerMwh ? 'error' : ''}
              />
              {errors.onsiteLoadPricePerMwh && <span className="error-message">{errors.onsiteLoadPricePerMwh}</span>}
            </div>
          </div>
        </div>

        {/* Optional Constraints */}
        <div className="form-section">
          <h3>Optional Constraints</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="pvMaxSizeMw">PV Max Size (MW)</label>
              <input
                type="number"
                id="pvMaxSizeMw"
                name="pvMaxSizeMw"
                value={formData.pvMaxSizeMw}
                onChange={handleInputChange}
                step="1"
                min="0"
                className={errors.pvMaxSizeMw ? 'error' : ''}
              />
              {errors.pvMaxSizeMw && <span className="error-message">{errors.pvMaxSizeMw}</span>}
              <small>Leave empty for no limit</small>
            </div>

            <div className="form-group">
              <label htmlFor="bessMaxSizeMwh">BESS Max Size (MWh)</label>
              <input
                type="number"
                id="bessMaxSizeMwh"
                name="bessMaxSizeMwh"
                value={formData.bessMaxSizeMwh}
                onChange={handleInputChange}
                step="1"
                min="0"
                className={errors.bessMaxSizeMwh ? 'error' : ''}
              />
              {errors.bessMaxSizeMwh && <span className="error-message">{errors.bessMaxSizeMwh}</span>}
              <small>Leave empty for no limit</small>
            </div>
          </div>
        </div>

        {errors.submit && (
          <div className="error-banner">
            {errors.submit}
          </div>
        )}

        <button type="submit" className="submit-button" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Run Optimization'}
        </button>
      </form>
    </div>
  );
}

export default UploadForm;
