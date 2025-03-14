import {Route, Routes} from "react-router";
import HomeLayout from "./components/layouts/HomeLayout.tsx";
import Home from "./pages/Home.tsx";
import LogIn from "./pages/LogIn.tsx";
import SignUp from "./pages/SignUp.tsx";
import DashboardLayout from "@/components/layouts/DashboardLayout.tsx";
import Dashboard from "@/pages/Dashboard.tsx";
import LogOut from "@/pages/LogOut.tsx";

function App() {
    return (
        <div>
            <Routes>
                <Route path="/" element={<HomeLayout />}>
                    <Route path="auth">
                        <Route path="log-in" element={<LogIn/>}/>
                        <Route path="sign-up" element={<SignUp/>}/>
                        <Route path="logout" element={<LogOut/>}/>
                    </Route>
                    <Route index element={<Home />}/>
                </Route>
                <Route path="dashboard" element={<DashboardLayout />}>
                    <Route index element={<Dashboard/>}/>
                </Route>
            </Routes>
        </div>
    );
}

export default App;