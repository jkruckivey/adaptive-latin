import { useNavigate } from 'react-router-dom'
import AdminDashboard from '../components/AdminDashboard'

export default function AdminPage() {
    const navigate = useNavigate()

    return (
        <div className="app admin-view">
            <div className="admin-close-header">
                <button onClick={() => navigate(-1)} className="close-admin-button">
                    ← Back
                </button>
            </div>
            <AdminDashboard />
        </div>
    )
}
