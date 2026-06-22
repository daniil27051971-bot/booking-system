import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { loginUser, registerUser } from "../api/authApi"
import "../styles/auth.css"

function Auth({ onAuth }) {
    const navigate = useNavigate()

    const [mode, setMode] = useState("login")

    const [username, setUsername] = useState("")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")

    async function handleLogin(event) {
        event.preventDefault()

        if (!username.trim() || !password.trim()) {
            alert("Введите логин и пароль")
            return
        }

        try {
            const data = await loginUser(username, password)

            localStorage.setItem("token", data.access_token)

            onAuth()
            navigate("/resources")
        } catch (error) {
            alert(error.response?.data?.detail || "Ошибка входа")
        }
    }

    async function handleRegister(event) {
        event.preventDefault()

        if (!username.trim() || !email.trim() || !password.trim()) {
            alert("Заполните все поля")
            return
        }

        try {
            await registerUser({
                username: username.trim(),
                email: email.trim(),
                password: password.trim(),
                role: "user"
            })

            const data = await loginUser(username, password)

            localStorage.setItem("token", data.access_token)

            alert("Регистрация успешна")
            onAuth()
            navigate("/resources")
        } catch (error) {
            alert(error.response?.data?.detail || "Ошибка регистрации")
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="auth-tabs">
                    <button
                        className={mode === "login" ? "active" : ""}
                        onClick={() => setMode("login")}
                    >
                        Вход
                    </button>

                    <button
                        className={mode === "register" ? "active" : ""}
                        onClick={() => setMode("register")}
                    >
                        Регистрация
                    </button>
                </div>

                <h1>{mode === "login" ? "Вход" : "Регистрация"}</h1>

                <form
                    className="auth-form"
                    onSubmit={mode === "login" ? handleLogin : handleRegister}
                >
                    <label>Логин</label>
                    <input
                        type="text"
                        value={username}
                        onChange={event => setUsername(event.target.value)}
                    />

                    {mode === "register" && (
                        <>
                            <label>Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={event => setEmail(event.target.value)}
                            />
                        </>
                    )}

                    <label>Пароль</label>
                    <input
                        type="password"
                        value={password}
                        onChange={event => setPassword(event.target.value)}
                    />

                    <button type="submit">
                        {mode === "login" ? "Войти" : "Зарегистрироваться"}
                    </button>
                </form>
            </div>
        </div>
    )
}

export default Auth