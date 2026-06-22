import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { registerUser } from "../api/authApi"
import "../styles/auth.css"

function Register() {
    const navigate = useNavigate()

    const [username, setUsername] = useState("")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")

    async function handleSubmit(event) {
        event.preventDefault()

        try {
            await registerUser({
                username: username,
                email: email,
                password: password,
                role: "user"
            })

            alert("Регистрация успешна")
            navigate("/")
        } catch (error) {
            alert(error.response?.data?.detail || "Ошибка регистрации")
        }
    }

    return (
        <div className="auth-page">
            <h1>Регистрация</h1>

            <form className="auth-form" onSubmit={handleSubmit}>
                <label>Логин</label>
                <input
                    type="text"
                    value={username}
                    onChange={event => setUsername(event.target.value)}
                />

                <label>Email</label>
                <input
                    type="email"
                    value={email}
                    onChange={event => setEmail(event.target.value)}
                />

                <label>Пароль</label>
                <input
                    type="password"
                    value={password}
                    onChange={event => setPassword(event.target.value)}
                />

                <button type="submit">Зарегистрироваться</button>
            </form>
        </div>
    )
}

export default Register