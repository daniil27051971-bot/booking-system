import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { loginUser } from "../api/authApi"
import "../styles/auth.css"

function Login() {
    const navigate = useNavigate()

    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")

    async function handleSubmit(event) {
        event.preventDefault()

        try {
            const data = await loginUser(username, password)
            localStorage.setItem("token", data.access_token)

            alert("Вход выполнен")
            navigate("/resources")
            window.location.reload()
        } catch (error) {
            alert(error.response?.data?.detail || "Ошибка входа")
        }
    }

    return (
        <div className="auth-page">
            <h1>Вход</h1>

            <form className="auth-form" onSubmit={handleSubmit}>
                <label>Логин</label>
                <input
                    type="text"
                    value={username}
                    onChange={event => setUsername(event.target.value)}
                />

                <label>Пароль</label>
                <input
                    type="password"
                    value={password}
                    onChange={event => setPassword(event.target.value)}
                />

                <button type="submit">Войти</button>
            </form>
        </div>
    )
}

export default Login