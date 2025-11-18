import OnboardingFlow from '../components/OnboardingFlow'

export default function OnboardingPage({ learnerName, courseTitle, courseMetadata, onComplete }) {
    return (
        <OnboardingFlow
            learnerName={learnerName}
            courseTitle={courseTitle}
            courseDomain={courseMetadata?.domain || ''}
            customQuestions={courseMetadata?.onboarding_questions}
            onComplete={onComplete}
        />
    )
}
