import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';

class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  List<User> _registeredUsers = [];

  User? _currentUser;


  static const String _usersKey = 'registered_users';
  static const String _currentUserKey = 'current_user';

  List<User> get registeredUsers => _registeredUsers;


  User? get currentUser => _currentUser;

  Future<void> initialize() async {
    await _loadUsers();
    await _loadCurrentUser();
  }

  Future<void> _loadUsers() async {
    final prefs = await SharedPreferences.getInstance();
    final String? usersJson = prefs.getString(_usersKey);
    
    if (usersJson != null) {
      final List<dynamic> usersList = jsonDecode(usersJson);
      _registeredUsers = usersList
          .map((json) => User.fromJson(json as Map<String, dynamic>))
          .toList();
    }
  }


  Future<void> _saveUsers() async {
    final prefs = await SharedPreferences.getInstance();
    final List<Map<String, dynamic>> usersJson =
        _registeredUsers.map((user) => user.toJson()).toList();
    await prefs.setString(_usersKey, jsonEncode(usersJson));
  }
  Future<void> _loadCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final String? currentUserJson = prefs.getString(_currentUserKey);
    
    if (currentUserJson != null) {
      final Map<String, dynamic> userMap = jsonDecode(currentUserJson);
      _currentUser = User.fromJson(userMap);
    }
  }


  Future<void> _saveCurrentUser(User? user) async {
    final prefs = await SharedPreferences.getInstance();
    
    if (user != null) {
      await prefs.setString(_currentUserKey, jsonEncode(user.toJson()));
    } else {
      await prefs.remove(_currentUserKey);
    }
  }


  Future<bool> register(String email, String password) async {
    if (_registeredUsers.any((user) => user.email == email)) {
      return false;
    }

    final newUser = User(email: email, password: password);
    _registeredUsers.add(newUser);
    
    await _saveUsers();
    
    return true;
  }


  Future<bool> login(String email, String password) async {
    try {

      _currentUser = _registeredUsers.firstWhere(
        (user) => user.email == email && user.password == password,
      );

      await _saveCurrentUser(_currentUser);
      
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<void> logout() async {
    _currentUser = null;
    await _saveCurrentUser(null);
  }


  bool isLoggedIn() {
    return _currentUser != null;
  }
}
