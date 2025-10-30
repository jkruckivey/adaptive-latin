import { useState } from 'react'
import './SelfAttestation.css'

function SelfAttestation({ attestationText, onComplete, materialTitle }) {
  const [isChecked, setIsChecked] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = () => {
    if (isChecked) {
      setSubmitted(true)
      setTimeout(() => {
        onComplete()
      }, 1000)
    }
  }

  if (submitted) {
    return (
      <div className="attestation-submitted">
        <div className="success-icon">✓</div>
        <h3>Attestation Confirmed</h3>
        <p>Thank you for confirming your engagement with this material.</p>
      </div>
    )
  }

  return (
    <div className="self-attestation">
      <div className="attestation-header">
        <h3>Confirm Your Engagement</h3>
        <p className="attestation-instruction">
          Please confirm that you have reviewed and understood the material.
        </p>
      </div>

      <div className="attestation-box">
        <label className="attestation-label">
          <input
            type="checkbox"
            checked={isChecked}
            onChange={(e) => setIsChecked(e.target.checked)}
            className="attestation-checkbox"
          />
          <span className="attestation-text">
            {attestationText}
          </span>
        </label>
      </div>

      <div className="attestation-actions">
        <button
          onClick={handleSubmit}
          disabled={!isChecked}
          className="confirm-button"
        >
          Confirm & Complete
        </button>
      </div>

      <div className="attestation-notice">
        <p>
          <strong>Academic Integrity:</strong> By checking this box, you are confirming
          that you have genuinely engaged with this material. Your honest participation
          is essential for your learning success.
        </p>
      </div>
    </div>
  )
}

export default SelfAttestation
