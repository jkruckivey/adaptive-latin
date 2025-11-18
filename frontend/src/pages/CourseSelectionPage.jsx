import { useNavigate } from 'react-router-dom'
import CourseSelector from '../components/CourseSelector'

export default function CourseSelectionPage({ onCourseSelected }) {
    const navigate = useNavigate()

    return (
        <CourseSelector
            onCourseSelected={onCourseSelected}
            onCreateCourse={() => navigate('/create-course')}
            onBack={() => navigate('/')}
        />
    )
}
