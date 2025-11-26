/**
 * Dashboard Screen - Mobile App
 *
 * Main dashboard view for Aurora Life mobile
 */
import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import Icon from 'react-native-vector-icons/Ionicons';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';

export default function DashboardScreen() {
  const { user } = useAuth();

  // Fetch dashboard data
  const { data, isLoading, refetch, isRefreshing } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => apiClient.get('/api/v1/dashboard'),
  });

  const predictions = data?.predictions || {};
  const insights = data?.insights || [];
  const recentEvents = data?.recent_events || [];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={isRefreshing} onRefresh={refetch} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.userName}>{user?.name || 'User'}!</Text>
        </View>
        <TouchableOpacity style={styles.notificationButton}>
          <Icon name="notifications-outline" size={24} color="#333" />
        </TouchableOpacity>
      </View>

      {/* Today's Predictions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Today's Predictions</Text>
        <View style={styles.predictionGrid}>
          <View style={[styles.predictionCard, { backgroundColor: '#FEF3C7' }]}>
            <Icon name="flash" size={32} color="#F59E0B" />
            <Text style={styles.predictionLabel}>Energy</Text>
            <Text style={styles.predictionValue}>
              {predictions.energy?.toFixed(1) || '7.5'}/10
            </Text>
          </View>
          <View style={[styles.predictionCard, { backgroundColor: '#DBEAFE' }]}>
            <Icon name="happy" size={32} color="#3B82F6" />
            <Text style={styles.predictionLabel}>Mood</Text>
            <Text style={styles.predictionValue}>
              {predictions.mood?.toFixed(1) || '8.2'}/10
            </Text>
          </View>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionGrid}>
          <TouchableOpacity style={styles.actionButton}>
            <Icon name="add-circle" size={24} color="#3B82F6" />
            <Text style={styles.actionLabel}>Add Event</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Icon name="moon" size={24} color="#8B5CF6" />
            <Text style={styles.actionLabel}>Log Sleep</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Icon name="fitness" size={24} color="#10B981" />
            <Text style={styles.actionLabel}>Exercise</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Icon name="restaurant" size={24} color="#F59E0B" />
            <Text style={styles.actionLabel}>Meal</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* AI Insights */}
      {insights.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI Insights</Text>
          {insights.map((insight: any, index: number) => (
            <View key={index} style={styles.insightCard}>
              <Icon name="bulb" size={20} color="#F59E0B" />
              <Text style={styles.insightText}>{insight.text}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Recent Activity */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          <TouchableOpacity>
            <Text style={styles.viewAllText}>View All</Text>
          </TouchableOpacity>
        </View>
        {recentEvents.map((event: any) => (
          <View key={event.id} style={styles.eventCard}>
            <View style={styles.eventIcon}>
              <Icon name={getEventIcon(event.type)} size={20} color="#3B82F6" />
            </View>
            <View style={styles.eventContent}>
              <Text style={styles.eventTitle}>{event.title}</Text>
              <Text style={styles.eventTime}>
                {new Date(event.event_time).toLocaleString()}
              </Text>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

function getEventIcon(type: string): string {
  const icons: Record<string, string> = {
    sleep: 'moon',
    exercise: 'fitness',
    work: 'briefcase',
    social: 'people',
    mood: 'happy',
    meal: 'restaurant',
  };
  return icons[type] || 'ellipse';
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
    marginTop: 16,
  },
  greeting: {
    fontSize: 16,
    color: '#6B7280',
  },
  userName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
  },
  notificationButton: {
    padding: 8,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  viewAllText: {
    color: '#3B82F6',
    fontSize: 14,
  },
  predictionGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  predictionCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  predictionLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
  },
  predictionValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 4,
  },
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  actionButton: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    width: '22%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  actionLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  insightCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFBEB',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    gap: 12,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    color: '#78350F',
  },
  eventCard: {
    flexDirection: 'row',
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  eventIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#EFF6FF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  eventContent: {
    flex: 1,
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
  },
  eventTime: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
});
