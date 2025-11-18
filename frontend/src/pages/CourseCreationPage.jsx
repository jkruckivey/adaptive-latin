import { useNavigate } from 'react-router-dom'
import CourseCreationWizard from '../components/course-creation/CourseCreationWizard'
import { api } from '../api'

export default function CourseCreationPage() {
    const navigate = useNavigate()

    const handleComplete = async (courseData) => {
        try {
            console.log('Creating course with data:', courseData)

            // Create the course with all metadata and concepts
            const result = await api.createCourse(courseData)
            console.log('Course created:', result)

            // If there are sources, add them to the course
            if (courseData.sources && courseData.sources.length > 0) {
                console.log(`Adding ${courseData.sources.length} sources...`)

                for (const source of courseData.sources) {
                    try {
                        // Determine if this is a course-level or concept-level source
                        if (source.scope === 'course') {
                            await api.addCourseSource(result.course_id, source)
                            console.log(`Added course-level source: ${source.title}`)
                        } else {
                            // Extract concept index from scope (e.g., "concept-0" -> 0)
                            const conceptIndex = parseInt(source.scope.replace('concept-', ''))
                            const conceptId = `concept-${String(conceptIndex + 1).padStart(3, '0')}`
                            await api.addConceptSource(result.course_id, conceptId, source)
                            console.log(`Added source to ${conceptId}: ${source.title}`)
                        }
                    } catch (sourceError) {
                        console.error('Error adding source:', sourceError)
                        // Continue adding other sources even if one fails
                    }
                }
            }

            alert(`Course "${courseData.title}" created successfully!`)
            navigate('/')
        } catch (error) {
            console.error('Error creating course:', error)
            alert(`Failed to create course: ${error.message}`)
        }
    }

    return (
        <CourseCreationWizard
            onComplete={handleComplete}
            onCancel={() => navigate('/')}
        />
    )
}
