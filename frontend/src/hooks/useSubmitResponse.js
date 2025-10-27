import { useState } from 'react'
import { api } from '../api'

/**
 * Custom hook to handle answer submission and response processing
 * Encapsulates common logic for both confidence and non-confidence submissions
 */
export function useSubmitResponse() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const submitResponse = async ({
    learnerId,
    questionType,
    answer,
    correctAnswer,
    confidence,
    conceptId,
    questionText,
    scenario,
    options,
    onSuccess
  }) => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await api.submitResponse(
        learnerId,
        questionType,
        answer,
        correctAnswer,
        confidence,
        conceptId,
        questionText,
        scenario,
        options
      )

      if (result.next_content) {
        // Attach debug info to content for debugging display
        const contentWithDebug = {
          ...result.next_content,
          debug_context: result.debug_context
        }

        // Call success callback with the content AND mastery data
        if (onSuccess) {
          onSuccess(contentWithDebug, {
            masteryScore: result.mastery_score,
            masteryThreshold: result.mastery_threshold,
            assessmentsCount: result.assessments_count,
            conceptCompleted: result.concept_completed
          })
        }

        return { success: true, content: contentWithDebug, mastery: {
          masteryScore: result.mastery_score,
          masteryThreshold: result.mastery_threshold,
          assessmentsCount: result.assessments_count,
          conceptCompleted: result.concept_completed
        }}
      } else {
        setError('Failed to get next content')
        return { success: false, error: 'Failed to get next content' }
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Failed to submit response:', err)
      return { success: false, error: err }
    } finally {
      setIsLoading(false)
    }
  }

  return {
    submitResponse,
    isLoading,
    error,
    setError
  }
}
