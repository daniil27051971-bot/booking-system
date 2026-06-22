import { Navigate } from "react-router-dom"

function ProtectedRoute({ children }) {
    const token = localStorage.getItem("token")

    if (!token) {
        alert("Сначала войдите в аккаунт")
        return <Navigate to="/" replace />
    }

    return children
}

export default ProtectedRoute