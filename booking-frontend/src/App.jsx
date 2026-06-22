import { Routes, Route, Link, Navigate, useNavigate } from "react-router-dom"
import { useState } from "react"

import Auth from "./pages/Auth"
import Resources from "./pages/Resources"
import BookingCreate from "./pages/BookingCreate"
import MyBookings from "./pages/MyBookings"
import ProtectedRoute from "./components/ProtectedRoute"

import "./styles/App.css"

function App() {
    const navigate = useNavigate()
    const [isAuth, setIsAuth] = useState(Boolean(localStorage.getItem("token")))

    function handleLogout() {
        localStorage.removeItem("token")
        setIsAuth(false)
        navigate("/auth")
    }

    return (
        <>
            <nav className="top-nav">
                {!isAuth && (
                    <Link to="/auth">Вход / Регистрация</Link>
                )}

                <Link to="/resources">Ресурсы</Link>

                {isAuth && (
                    <>
                        <Link to="/my-bookings">Мои бронирования</Link>
                        <Link to="/booking/new">Создать бронь</Link>

                        <button onClick={handleLogout} className="logout-btn">
                            Выйти
                        </button>
                    </>
                )}
            </nav>

            <Routes>
                <Route path="/" element={<Navigate to="/resources" />} />
                <Route path="/auth" element={<Auth onAuth={() => setIsAuth(true)} />} />
                <Route path="/resources" element={<Resources />} />

                <Route
                    path="/my-bookings"
                    element={
                        <ProtectedRoute>
                            <MyBookings />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/booking/new"
                    element={
                        <ProtectedRoute>
                            <BookingCreate />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/booking/new/:resourceId"
                    element={
                        <ProtectedRoute>
                            <BookingCreate />
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </>
    )
}

export default App